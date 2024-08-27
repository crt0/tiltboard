BASE_DIR = ARG1
DATA_FILE = BASE_DIR.'/data.txt'
set terminal png notransparent rounded font helvetica 16 size 1600,1200
set output BASE_DIR.'/plot.png'
set xdata time
set format x "%a\n%m/%d\n%H:%M" timedate
set xtics timedate
set xtics 60. * 60. * 24.
set y2tics
set y2range [45.:95.]
# set datafile missing NaN

set style line 1 lt 1 lc rgb "#009051" lw 3 pt 2 ps 1.2
set style line 2 lt 1 lc rgb "#0096FF" lw 3 pt 1 ps 1.2
set style line 3 lt 1 lc rgb "#CC0000" lw 2 pt 6 ps 3

set style line 11 lc rgb '#808080' lt 1 lw 3
set border 0 back ls 11
set tics out nomirror

set style line 12 lc rgb '#808080' lt 0 lw 1
set grid back ls 12

plot DATA_FILE using (timecolumn(1,'%s')):2 smooth bezier ls 1 t 'Gravity', \
     DATA_FILE using (timecolumn(1,'%s')):3 smooth bezier ls 2 t 'Temperature' axes x1y2, \
     DATA_FILE using (timecolumn(1,'%s')):2:(exists($4)?$4:1/0) \
                     with labels point ls 3 left offset 1,1 notitle

set terminal png notransparent rounded font helvetica 14 size 1400,1050
set output BASE_DIR.'/plot-1400x1050.png'
replot

set terminal png notransparent rounded font helvetica 12 size 992,744
set output BASE_DIR.'/plot-992x744.png'
replot

set terminal png notransparent rounded font helvetica 8 size 376,282
set output BASE_DIR.'/plot-376x282.png'
replot
