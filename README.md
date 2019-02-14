The virtual env for this is tvid and was set up like:

`brew install tcl-tk`
`export CPPFLAGS="-I/usr/local/opt/tcl-tk/include"`
`export LDFLAGS="-L/usr/local/opt/tcl-tk/lib"`
`pyenv install 3.7.2`
`mkvirtualenv tvid -p ~/.pyenv/versions/3.7.2/bin/python`
`pip install -r requirements.txt`