module.exports = function(grunt) {

  // Initializing the configuration object
  grunt.initConfig({

    less: {
      development: {
        options: {
          compress: true
        },
        files: {
          "./ivweb/app/static/dist/everything.css": "./ivweb/app/static/less/everything.less"
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
              'bower_components/moment/min/moment.min.js',
              'bower_components/jquery/dist/jquery.min.js',
              'bower_components/jquery/dist/jquery.min.map',
              'bower_components/jquery-ui/jquery-ui.min.js',
              'bower_components/jquery-pjax/jquery.pjax.js',
              'bower_components/font-awesome/fonts/**',
              'bower_components/html5shiv/dist/html5shiv.min.js',
              'bower_components/respond/dest/respond.min.js',
              'bower_components/jquery-number/jquery.number.min.js',
              'bower_components/d3/d3.min.js',
              'bower_components/nvd3/build/nv.d3.min.js',
              'bower_components/nvd3/build/nv.d3.css',
              'ivweb/app/static/js/**',
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
      less: {
        files: [
            // all the watched files...
            './ivweb/app/static/less/*.less',
        ],
        tasks: ['less'], //tasks to run
        options: {
          livereload: true
        }
      },
      copy: {
        files: [
            // everything except less...
            './ivweb/app/static/js/**',
            './ivweb/app/static/images/**',
            './ivweb/app/static/ico/**',
            'ivweb/app/static/css/**',
            'ivweb/app/static/fonts/**',
            'ivweb/app/static/pdf/**',
            './bower_components/**'
        ],
        tasks: ['copy'], // tasks to run
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

  // Task definition
  grunt.registerTask('build', ['copy', 'less']);
  grunt.registerTask('default', ['build', 'watch']);
};