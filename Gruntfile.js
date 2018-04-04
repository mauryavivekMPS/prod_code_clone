module.exports = function(grunt) {

  grunt.initConfig({

    concat: {
      options: {
        separator: '\n\n;\n\n'
      },
      dist: {
        src: ['./ivweb/app/static/js/**'],
        dest: './ivweb/app/static/dist/common.js'
      }
    },

    less: {
      development: {
        options: {
          compress: true
        },
        files: {
          "./ivweb/app/static/dist/everything-2018-04-04.css": "./ivweb/app/static/less/everything.less"
        }
      }
    },

    copy: {
      main: {
        files: [
          {
            expand: true,
            src: [
              'bower_components/bootstrap/dist/js/bootstrap.min.js',
              'bower_components/bootstrap-datepicker/dist/css/bootstrap-datepicker3.min.css',
              'bower_components/bootstrap-datepicker/dist/css/bootstrap-datepicker3.css.map',
              'bower_components/bootstrap-datepicker/dist/js/bootstrap-datepicker.min.js',
              'bower_components/bootstrap3-typeahead/bootstrap3-typeahead.min.js',
              'bower_components/bootstrap-multiselect/dist/css/bootstrap-multiselect.css',
              'bower_components/bootstrap-multiselect/dist/js/bootstrap-multiselect.js',
              'bower_components/moment/min/moment.min.js',
              'bower_components/jquery/dist/jquery.min.js',
              'bower_components/jquery/dist/jquery.min.map',
              'bower_components/jquery-ui/jquery-ui.min.js',
              'bower_components/jquery-pjax/jquery.pjax.js',
              'bower_components/font-awesome/fonts/**',
              'bower_components/html5shiv/dist/html5shiv.min.js',
              'bower_components/respond/dest/respond.min.js',
              'bower_components/jquery-number/jquery.number.min.js',
              'bower_components/jquery-number/jquery.number.min.js.map',
              'bower_components/jquery-cookie/jquery.cookie.js',
              'ivweb/app/static/images/**',
              'ivweb/app/static/ico/**',
              'ivweb/app/static/css/**',
              'ivweb/app/static/fonts/**',
              'ivweb/app/static/pdf/**'
            ],
            dest: './ivweb/app/static/dist/',
            filter: 'isFile',
            flatten: true
          }
        ]
      }
    },

    clean: ['./ivweb/app/static/dist'],

    watch: {
      concat: {
        files: [
          './ivweb/app/static/js/**'
        ],
        tasks: ['concat'],
        options: {
          livereload: true
        }
      },

      less: {
        files: [
            './ivweb/app/static/less/*.less'
        ],
        tasks: ['less'],
        options: {
          livereload: true
        }
      },
      copy: {
        files: [
            // everything except less and js...
            './ivweb/app/static/images/**',
            './ivweb/app/static/ico/**',
            './ivweb/app/static/css/**',
            './ivweb/app/static/fonts/**',
            './ivweb/app/static/pdf/**',
            './bower_components/**'
        ],
        tasks: ['copy'],
        options: {
          livereload: true
        }
      }
    }
  });

  // Plugin loading
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-contrib-concat');

  // Task definition
  grunt.registerTask('build', ['concat', 'copy', 'less']);
  grunt.registerTask('default', ['build', 'watch']);
};
