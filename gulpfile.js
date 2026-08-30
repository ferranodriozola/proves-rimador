const gulp = require('gulp');
const sass = require('gulp-sass')(require('sass'));
const cleanCSS = require('gulp-clean-css');
const uglify = require('gulp-uglify');
const concat = require('gulp-concat');
const rename = require('gulp-rename');
const sourcemaps = require('gulp-sourcemaps');

// CSS del lloc. Tot css/*.scss va a parar a UN sol full, que es baixen
// totes les pagines menys el joc.
gulp.task('styles', function () {
    return gulp.src(['css/**/*.scss', '!css/**/_*.scss'], { allowEmpty: true })
        .pipe(sourcemaps.init())
        .pipe(sass().on('error', sass.logError))
        .pipe(concat('styles.css'))
        .pipe(gulp.dest('dist/css'))
        .pipe(cleanCSS())
        .pipe(rename({ suffix: '.min' }))
        .pipe(sourcemaps.write('.'))
        .pipe(gulp.dest('dist/css'));
});

// CSS del joc. Full a part, i no pas una entrada mes de la tasca de sobre:
// aquella fa concat() de tot el que troba, i el joc te regles damunt de html,
// body, a i * que es barallarien amb les del lloc (i a l'inreves: el
// general.scss posa height:100% i overflow:hidden al body, que li trencaria el
// desplacament al joc). Comparteixen el css/_variables.scss i prou.
gulp.task('styles-joc', function () {
    return gulp.src('joc/css/joc.scss', { allowEmpty: true })
        .pipe(sourcemaps.init())
        .pipe(sass().on('error', sass.logError))
        .pipe(gulp.dest('dist/css'))
        .pipe(cleanCSS())
        .pipe(rename({ suffix: '.min' }))
        .pipe(sourcemaps.write('.'))
        .pipe(gulp.dest('dist/css'));
});

// JS 
gulp.task('scripts', function () {
    return gulp.src('js/**/*.js', { allowEmpty: true }) 
        .pipe(sourcemaps.init())
        .pipe(gulp.dest('dist/js'))  
        .pipe(uglify().on('error', console.error))
        .pipe(rename({ suffix: '.min' }))  
        .pipe(sourcemaps.write('.'))
        .pipe(gulp.dest('dist/js'));  
});

gulp.task('build', gulp.series('styles', 'styles-joc', 'scripts'));

gulp.task('watch', function () {
    // El _variables.scss el comparteixen els dos fulls: tocar-lo ha de refer
    // tots dos, i per aixo surt a les dues vigilancies.
    gulp.watch('css/**/*.scss', gulp.series('styles', 'styles-joc'));
    gulp.watch('joc/css/*.scss', gulp.series('styles-joc'));
    gulp.watch('js/**/*.js', gulp.series('scripts'));
});

gulp.task('default', gulp.series('build'));

gulp.task('dev', gulp.series('build', 'watch'));