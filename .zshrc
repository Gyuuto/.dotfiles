# Set up the prompt

export TERM=xterm-256color

if [[ $TERM = dumb ]]; then
  unset zle_bracketed_paste
fi

if [[ ! -d ~/.zplug ]]; then
    git clone https://github.com/zplug/zplug ~/.zplug
fi

source ~/.zplug/init.zsh 
zplug "zsh-users/zsh-syntax-highlighting"
zplug "zsh-users/zsh-completions"
zplug "chrissicool/zsh-256color"
zplug "zplug/zplug", hook-build:"zplug --self-manage"

zplug load --verbose
zplug check || zplug install

autoload -Uz promptinit
promptinit
prompt redhat
setopt histignorealldups sharehistory

# Use emacs keybindings even if our EDITOR is set to vi
bindkey -e
bindkey '^[[1;5C' emacs-forward-word
bindkey '^[[1;5D' emacs-backward-word
bindkey ';5C' forward-word
bindkey ';5D' backward-word

# Keep 1000 lines of history within the shell and save it to ~/.zsh_history:
HISTSIZE=1000
SAVEHIST=1000
HISTFILE=~/.zsh_history

# Use modern completion system
if [[ "$EMACS" != "" ]]; then
    autoload -Uz compinit
    compinit

    zstyle ':completion:*' auto-description 'specify: %d'
    zstyle ':completion:*' completer _expand _complete _correct _approximate
    zstyle ':completion:*' format 'Completing %d'
    zstyle ':completion:*' group-name ''
    zstyle ':completion:*' menu select=2
    eval "$(dircolors -b)"
    zstyle ':completion:*:default' list-colors ${(s.:.)LS_COLORS}
    zstyle ':completion:*' list-colors ''
    zstyle ':completion:*' list-prompt %SAt %p: Hit TAB for more, or the character to insert%s
    zstyle ':completion:*' matcher-list '' 'm:{a-z}={A-Z}' 'm:{a-zA-Z}={A-Za-z}' 'r:|[._-]=* r:|=* l:|=*'
    zstyle ':completion:*' menu select=long
    zstyle ':completion:*' select-prompt %SScrolling active: current selection at %p%s
    zstyle ':completion:*' use-compctl false
    zstyle ':completion:*' verbose true

    zstyle ':completion:*:*:kill:*:processes' list-colors '=(#b) #([0-9]#)*=0=01;31'
    zstyle ':completion:*:kill:*' command 'ps -u $USER -o pid,%cpu,tty,cputime,cmd'
fi

## for open mpi
# export PATH=${PATH}:/opt/openmpi-1.10.2_icc/bin
# export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/openmpi-1.10.2_icc/lib

## using my installation
export PATH=/usr/local/bin:${PATH}
export LD_LIBRARY_PATH=/usr/local/lib:${PATH}

## for no-windowed emacs
alias emacs="emacs -nw"

## for intel
export MKLROOT=/opt/intel/composer_xe_2015.0.090/mkl
export PATH=${PATH}:/opt/intel/composer_xe_2015.0.090/bin/intel64:/opt/intel/impi_5.0.1/bin64
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/opt/intel/mkl/lib/intel64:/opt/intel/lib/intel64

## for OpenBLAS
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/opt/OpenBLAS/lib

## for clBLAS
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/local/lib64

# added by Anaconda2 4.3.0 installer
export PATH="/home/yuto/anaconda2/bin:$PATH"

# added by Anaconda3 4.3.0 installer
export PATH="/home/yuto/anaconda3/bin:$PATH"

# for amd gpu
alias amd_status="aticonfig --odgt --odgc"
