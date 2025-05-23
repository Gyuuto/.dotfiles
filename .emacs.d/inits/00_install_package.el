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
    vue-mode
    typescript-mode
    csharp-mode

    ;;; useful for programming
    smart-compile
    auto-complete
    company
    company-irony
    irony
    eglot
    eglot-inactive-regions
    ;; lsp-mode
    ;; lsp-ui
    ;company-lsp
    ;;cquery
    ccls
    magit
    highlight-symbol
    expand-region
    region-bindings-mode
    cmake-ide
    rainbow-delimiters
    flymake
    flymake-diagnostic-at-point
    ;; ivy-posframe
    ;; flycheck
    ;; flycheck-rust
    ;; flycheck-irony
    ;; flycheck-popup-tip
    racer

    ;;; shell ?
    shell-command+
    exec-path-from-shell

    ;;; useful for buffer
    popwin
    ace-window

    ;;;; helm
    helm
    helm-swoop
    helm-git-grep
    helm-gtags
    helm-ls-git
    helm-xref

    ;;;; ivy
    ivy
    ivy-xref
    ivy-hydra
    counsel
    counsel-tramp
    swiper
    smex

    ;;; LLM
    ;; llm
    ;; ellama
    gptel

    ;;; etc
    yatex
    ansi-color
    orgtbl-aggregate
    ))

(let ((not-installed (loop for x in installing-package-list
			   when (not (package-installed-p x))
			   collect x)))
  (when not-installed
    (package-refresh-contents)
    (dolist (pkg not-installed)
      (package-install pkg))))
