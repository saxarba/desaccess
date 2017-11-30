(function(document) {
  'use strict';

  var app = document.querySelector('#app');

  app.baseUrl = '/';
  if (window.location.port === '') {  // if production
  };


  window.addEventListener('WebComponentsReady', function() {
    var pages = document.getElementById("mainPages");
    var menu = document.querySelector('paper-menu');
    app.selection="0";
    pages.select("0");
    menu.select("0");
    // pages.selected="0";
    // menu.selected="0";
        menu.addEventListener('iron-select', function() {
            app.selection=menu.selected;
            // pages.selected=menu.selected;
            pages.select(menu.selected)
            app.editor.refresh();
            if (app.$.drawerLayout.narrow) {app.$.drawer.close();}
        });
        menu.addEventListener('iron-activate', function() {
           //app.$.drawer.close();
        });

        myQuery = document.getElementById("queryBox");
        app.editor = CodeMirror.fromTextArea(myQuery, {
            lineNumbers: true,
            mode: 'text/x-plsql',
            autofocus: true,
        });
        app.editor.setValue('-- Insert Query --\n');
        app.editor.focus();
        app.editor.execCommand('goLineDown');
        myJobQuery = document.getElementById("jobQueryBox");
        app.jobquerybox = CodeMirror.fromTextArea(myJobQuery, {
            lineNumbers: false,
            mode: 'text/x-plsql',
            readOnly: true,
            autofocus: true,
        });
        app.jobquerybox.setValue('\n\n\n\n\n\n\n\n\n\n');
        app.jobquerybox.focus();
        myExampleQuery = document.getElementById("exampleQueryBox");
        app.examplequerybox = CodeMirror.fromTextArea(myExampleQuery, {
            lineNumbers: false,
            mode: 'text/x-plsql',
            readOnly: true,
            autofocus: true,
            viewportMargin: 50,
        });
        app.examplequerybox.setValue('\n\n\n\n\n\n\n\n\n\n\n');
        app.examplequerybox.focus();

        var xsize = document.getElementById("xsizeSlider");
               xsize.addEventListener('value-change', function() {
                   document.getElementById("xsizeLabel").textContent = xsize.value;
               });
               var ysize = document.getElementById("ysizeSlider");
               ysize.addEventListener('value-change', function() {
                   document.getElementById("ysizeLabel").textContent = ysize.value;
               });



  });



})(document);
