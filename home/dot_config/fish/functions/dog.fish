function dog --description 'Scratchpad -> clipboard (OSC 52).'
    set -l dir /tmp/scratch-$USER
    mkdir -p $dir

    set -l name (test -n "$argv[1]"; and echo $argv[1]; or echo default)
    set -l file $dir/$name.md
    set -l ed (test -n "$EDITOR"; and echo $EDITOR; or echo vim)

    if isatty stdin
        $ed $file
    else
        # Piped stdin: overwrite with it, then point the editor at the terminal
        cat >$file
        $ed $file </dev/tty
    end
    set -gx DOG $file

    if test -s $file
        # OSC 52: hand base64 text to the terminal emulator, which sets the local clipboard
        printf '\e]52;c;%s\a' (string collect <$file | base64 -w0) >/dev/tty
    end
end
