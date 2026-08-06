const gulp = require('gulp');
const sass = require('gulp-sass')(require('sass'));
const cleanCSS = require('gulp-clean-css');
const uglify = require('gulp-uglify');
const concat = require('gulp-concat');
const rename = require('gulp-rename');
const sourcemaps = require('gulp-sourcemaps');

// CSS
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

gulp.task('build', gulp.series('styles', 'scripts'));

gulp.task('watch', function () {
    gulp.watch('css/**/*.scss', gulp.series('styles'));
    gulp.watch('js/**/*.js', gulp.series('scripts'));
});

gulp.task('default', gulp.series('build'));

gulp.task('dev', gulp.series('build', 'watch'));