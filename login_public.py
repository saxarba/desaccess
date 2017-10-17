import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import Settings
from oracle import db_utils
import cx_Oracle
import os
import time
import json
import yaml
from version import __version__

dbConfig0 = Settings.dbConfig()


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("usera")


class SignupHandler(BaseHandler):
    def get(self):
        self.render('signup.html', errormessage='', toast='no')

    def post(self):
        username = self.get_argument("username", "").lower()
        password = self.get_argument("password", "")
        firstname = self.get_argument("firstname", "")
        lastname = self.get_argument("lastname", "")
        email = self.get_argument("email", "")
        ## SHOULD CHECK username and email
        if db_utils.check_username(username):
            db_utils.create_user(username, password, firstname, lastname, email, '', '')
            check, url = db_utils.create_reset_url(email)
            print('localhost:8080/easyweb/activate/{}'.format(url))
            self.write(json.dumps({'msg': 'Activation email sent! {}'.format(url), 'errno': '0'}))
        else:
            print('Username already exists')
            self.write(json.dumps({'msg': '{0} already exists.'
                                          'Try a differnt one'.format(username), 'errno': '1'}))

class ResetHandler(BaseHandler):
    def get(self, slug):
        username, msg = db_utils.valid_url(slug, 3600)
        if username is not None:
            self.render('reset.html', errormessage='', toast='no', url=slug, user=username)
        else:
            self.write(msg)
    def post(self):
        email = self.get_argument("email", "")
        print(email)
        print('Reset Password')
        check, url = db_utils.create_reset_url(email)
        print(url)
        time.sleep(5)
        print('5 secs passed')
        if check:
            self.write(json.dumps({'msg': 'Activation email sent! {}'.format(url), 'errno': '0'}))
        else:
            self.write(json.dumps({'msg': '{}'.format(url), 'errno': '1'}))
    def put(self):
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        url = self.get_argument("url", "")
        print(username, password, url)
        username2, msg = db_utils.valid_url(url, 3600+60)
        print(username2, msg)
        if username == username2:
            db_utils.update_password(username, password)
            db_utils.unlock_user(username)
            # DELETE URL
            self.write(json.dumps({'msg': 'Password updated', 'errno': '0'}))
        else:
            self.write(json.dumps({'msg': 'Something went wrong', 'errno': '1'}))







class ActivateHandler(BaseHandler):
    def get(self, slug):
        username, msg = db_utils.valid_url(slug, 9000)
        if username is not None:
            self.write('<h1> Thanks for activate {}<h1> <br> <a href="/"> Home </a> '.format(username))
            db_utils.unlock_user(username)
        else:
            self.write(msg)

class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        #self.render("main.html", name='Matias', email='', username='mcarras2') #TODO
        loc_passw = self.get_secure_cookie("userb").decode('ascii').replace('\"', '')
        loc_user = self.get_secure_cookie("usera").decode('ascii').replace('\"', '')
        loc_db = self.get_secure_cookie("userdb").decode('ascii').replace('\"', '')
        newfolder = os.path.join(Settings.WORKDIR, loc_user)
        if not os.path.exists(newfolder):
            os.mkdir(newfolder)
        kwargs = {'host': dbConfig0.host, 'port': dbConfig0.port, 'service_name': loc_db}
        dsn = cx_Oracle.makedsn(**kwargs)
        with open('config/user_manager.yaml', 'r') as cfile:
            conf = yaml.load(cfile)['oracle']
        user_manager = conf['user']
        pass_manager = conf['passwd']
        del conf
        dbh = cx_Oracle.connect(user_manager, pass_manager, dsn=dsn)
        cursor = dbh.cursor()
        try:
            cc = cursor.execute('select firstname,lastname,email from des_admin.des_users where '
                                'upper(username) = \'%s\'' % loc_user.upper()).fetchone()
        except:
            cc = ('', '', '')
        cursor.close()
        dbh.close()
        self.render("main-public.html", name=cc[0], lastname=cc[1], email=cc[2], username=loc_user, db=loc_db)


class AuthLoginHandler(BaseHandler):
    def get(self):
        update = 'no'
        toast = 'no'
        try:
            errormessage = self.get_argument("error")
            print(errormessage)
            if '28001' in errormessage:
                update = 'yes'
                errormessage += ". Please enter new password."
        except:
            errormessage = ""
        try:
            db = self.get_argument("db")
            print(db)
        except:
            db = ""
        self.render("login-public.html", errormessage=errormessage, version=__version__, update=update,
                    toast=toast, db=db)

    def check_permission(self, password, username, db):
        #return True, "" #TODO
        kwargs = {'host': dbConfig0.host, 'port': dbConfig0.port, 'service_name': db}
        dsn = cx_Oracle.makedsn(**kwargs)
        try:
            dbh = cx_Oracle.connect(username, password, dsn=dsn)
            dbh.close()
            return True, ""
        except Exception as e:
            error = str(e).strip()
            return False, error

    def post(self):
        username = self.get_argument("username", "")
        password = self.get_argument("password", "")
        db = self.get_argument("database", "")
        auth, err = self.check_permission(password, username, db)
        if auth:
            self.set_current_user(username, password, db)
            newfolder = os.path.join(Settings.WORKDIR, username)
            if not os.path.exists(newfolder):
                os.mkdir(newfolder)
            # Add to DB for stats
            self.redirect(self.get_argument("next", u"/easyweb/"))
        else:
            error_msg = u"?error=" + tornado.escape.url_escape(err)
            db_msg = u";db=" + tornado.escape.url_escape(db)
            self.redirect(u"/easyweb/login/" + error_msg + db_msg)

    def set_current_user(self, user, passwd, db):
        if user:
            self.set_secure_cookie("usera", tornado.escape.json_encode(user), expires_days=5)
            self.set_secure_cookie("userb", tornado.escape.json_encode(passwd), expires_days=5)
            self.set_secure_cookie("userdb", tornado.escape.json_encode(db), expires_days=5)
        else:
            self.clear_cookie("usera")
            self.clear_cookie("userb")
            self.clear_cookie("userdb")


class UpdateInfoHandler(BaseHandler):
    def post(self):
        with open('config/user_manager.yaml', 'r') as cfile:
            conf = yaml.load(cfile)['oracle']
        user_manager = conf['user']
        pass_manager = conf['passwd']
        del conf
        username = self.get_argument("username", "")
        firstname = self.get_argument("firstname", "")
        lastname = self.get_argument("lastname", "")
        email = self.get_argument("email", "")
        err=''
        db_utils.update_info(username, firstname, lastname, email, user_manager, pass_manager)
        return self.write(json.dumps({'msg': err, 'errno': '0'}))





class ChangeAuthHandler(BaseHandler):

    def check_permission_new(self, oldpassword, password, username, db):
        #return True, "" #TODO
        kwargs = {'host': dbConfig0.host, 'port': dbConfig0.port, 'service_name': db}
        dsn = cx_Oracle.makedsn(**kwargs)
        try:
            dbh = cx_Oracle.connect(username, oldpassword, dsn=dsn, newpassword=password)
            dbh.close()
            return True, ""
        except Exception as e:
            error = str(e).strip()
            return False, error

    def post(self):
        username = self.get_argument("username", "")
        oldpassword = self.get_argument("oldpassword", "")
        password = self.get_argument("password", "")
        db = self.get_argument("database", "")
        auth, err = self.check_permission_new(oldpassword, password, username, db)
        if auth:
            self.clear_cookie("usera")
            self.clear_cookie("userb")
            self.clear_cookie("userdb")
            return self.write(json.dumps({'msg': err, 'errno': '0'}))
        else:
            return self.write(json.dumps({'msg': err, 'errno': '1'}))

    def set_current_user(self, user, passwd, db):
        if user:
            self.set_secure_cookie("usera", tornado.escape.json_encode(user), expires_days=5)
            self.set_secure_cookie("userb", tornado.escape.json_encode(passwd), expires_days=5)
            self.set_secure_cookie("userdb", tornado.escape.json_encode(db), expires_days=5)
        else:
            self.clear_cookie("usera")
            self.clear_cookie("userb")
            self.clear_cookie("userdb")


class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("usera")
        self.clear_cookie("userb")
        self.clear_cookie("userdb")
        self.redirect(self.get_argument("next", "/easyweb/"))
