(require 'cl)

(defvar installing-package-list
  '(
    ;; ここに使っているパッケージを書く。
    ;;; mode
    jade-mode
    web-mode
    cuda-mode
    cmake-mode
    matlab-mode
    markdown-mode
    yaml-mode
    meghanada
    rust-mode
    ;;; useful for programming
    smart-compile
    auto-complete
    company
    company-irony
    irony
    magit
    highlight-symbol
    expand-region
    region-bindings-mode
    rtags
    cmake-ide
    rainbow-delimiters
    flycheck
    flycheck-rust
    flycheck-irony
    racer
    ;;; shell ?
    shell-command
    exec-path-from-shell
    ;;; useful for buffer
    ;; anything
    popwin
    helm
    helm-git-grep
    helm-gtags
    helm-ls-git
    ;;; etc
    yatex
    ansi-color
    ))

(let ((not-installed (loop for x in installing-package-list
			   when (not (package-installed-p x))
			   collect x)))
  (when not-installed
    (package-refresh-contents)
    (dolist (pkg not-installed)
      (package-install pkg))))
