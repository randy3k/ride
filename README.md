# Role: A 21 century R console

Role is a modern **R** cons**ole** with a handful of features allow R programming faster.

Note: _Role_ is very new, users should use it at their own risks. 

<img width="500px" src="https://cloud.githubusercontent.com/assets/1690993/24591455/773e3478-17cf-11e7-8cac-a76ae03d4cf5.png"></img>


### Features

Progress

- [x] multiline editing
- [x] brackted paste mode
- [x] syntax highlight
- [ ] auto completion
- [x] lightwight, no compilation is required
- [x] cross-platform, work on ~~Windows~~, macOS and Linux
- [x] robust, run on both Python 2 and 3
- [ ] allow custom color scheme
- [ ] highlight output
- [ ] object viewer
- [ ] a backdoor to allow other programs to communicate with Role.

### Installation

Requirements:

- The installation of R is required to use _Role_, R installation binary can be downloaded from https://cran.r-project.org.
- `python` is also required to install _Role_. If your system doesn't come with a python distribution, it can be downloaded from https://conda.io/miniconda.html. Both version 2 and version 3 should work.
- `pip` is optional but it makes the installation a bit easier.

```sh
# install released version
pip install role
# or the development version
pip install git+https://github.com/randy3k/role
```

### Troubleshooting

If _Role_ cannot locate the R installation files automatically. You can either expose the R binary to the system `PATH` variable or export the environment variable `R_HOME`. For example,

```sh
$ export R_HOME=/usr/local/lib/R
$ role  
```

### Caveat

_Role_ is written in pure python and built on the [prompt-toolkit](https://github.com/jonathanslenders/python-prompt-toolkit) and _Role_ has a minimal dependency of `six`, `wcwidth`, `prompt-toolkit`, `pygments` and `pyzmq`.