function doge --description 'Browse scratchpads in yazi, pick one to edit + copy. dog, explored.'
    set -l dir /tmp/scratch-$USER
    mkdir -p $dir

    set -l choice (mktemp)
    yazi $dir --chooser-file=$choice
    set -l file (cat $choice | head -1)
    rm -f $choice
    test -z "$file"; and return

    dog (path basename $file | string replace -r '\.md$' '')
end
