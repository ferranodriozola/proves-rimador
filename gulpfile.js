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
//
// HI HA MES D'UNA CARPETA DE JOC mentre es refa: joc/ es el que hi ha publicat i
// joc2/ el que el substituira. Cadascuna te el SEU full (les classes no son les
// mateixes) i, per tant, la seva sortida: el nom de la carpeta mana, o sigui que
// joc/css/joc.scss -> dist/css/joc.min.css i joc2/css/joc.scss ->
// dist/css/joc2.min.css. Cada index.html demana el que li toca.
//
// EL DIA QUE joc/ S'ESBORRI i joc2/ passi a dir-se joc, aquesta llista es queda
// amb 'joc' i el <link> de joc/index.html torna a dir dist/css/joc.min.css: no
// hi ha res mes a canviar.
const CARPETES_DEL_JOC = ['joc', 'joc2'];

function fullDelJoc(carpeta) {
    return function () {
        return gulp.src(`${carpeta}/css/joc.scss`, { allowEmpty: true })
            .pipe(sourcemaps.init())
            .pipe(sass().on('error', sass.logError))
            .pipe(rename({ basename: carpeta }))
            .pipe(gulp.dest('dist/css'))
            .pipe(cleanCSS())
            .pipe(rename({ suffix: '.min' }))
            .pipe(sourcemaps.write('.'))
            .pipe(gulp.dest('dist/css'));
    };
}

gulp.task('styles-joc', gulp.parallel(
    ...CARPETES_DEL_JOC.map((carpeta) => {
        const tasca = fullDelJoc(carpeta);
        Object.defineProperty(tasca, 'name', { value: `styles-${carpeta}` });
        return tasca;
    })
));

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
    gulp.watch(CARPETES_DEL_JOC.map((c) => `${c}/css/*.scss`), gulp.series('styles-joc'));
    gulp.watch('js/**/*.js', gulp.series('scripts'));
});

gulp.task('default', gulp.series('build'));

gulp.task('dev', gulp.series('build', 'watch'));