The virtual env for this is tennis and was set up like:

`brew install tcl-tk`
`export CPPFLAGS="-I/usr/local/opt/tcl-tk/include"`
`export LDFLAGS="-L/usr/local/opt/tcl-tk/lib"`
`pyenv install 3.7.2`
`mkvirtualenv tennis -p ~/.pyenv/versions/3.7.2/bin/python`
`pip install -r requirements.txt`

(2021-03-26: I would like to know what tcl-tk is used for?)

To use run:

`python tvs/splitter.py --video <path-to-video> --fps 240`

This will output a video in `tmp` (which can be changed by a 
parameter) with the important parts fo the video.