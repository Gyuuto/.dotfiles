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
    dockerfile-mode

    ;;; useful for programming
    smart-compile
    company
    company-irony
    irony
    eglot
    eglot-inactive-regions
    ccls
    magit
    highlight-symbol
    expand-region
    region-bindings-mode
    cmake-ide
    rainbow-delimiters
    flymake
    flymake-diagnostic-at-point
    racer

    ;;; shell ?
    shell-command+
    exec-path-from-shell

    ;;; useful for buffer
    popwin
    ace-window

    ;; ;;;; helm
    ;; helm
    ;; helm-swoop
    ;; helm-git-grep
    ;; helm-gtags
    ;; helm-ls-git
    ;; helm-xref

    ;; ;;;; ivy
    ;; ivy
    ;; ivy-xref
    ;; ivy-hydra
    ;; counsel
    ;; counsel-tramp
    ;; swiper
    ;; smex

    ;;;; vertico
    vertico
    marginalia
    embark
    embark-consult
    orderless

    ;;; LLM
    ;; llm
    ;; ellama
    gptel
    aidermacs
    minuet

    ;;; etc
    yatex
    ansi-color
    orgtbl-aggregate
    ))

(let ((not-installed (cl-loop for x in installing-package-list
			   when (not (package-installed-p x))
			   collect x)))
  (when not-installed
    (package-refresh-contents)
    (dolist (pkg not-installed)
      (package-install pkg))))

;; ;; use straigt.el
;; (defvar bootstrap-version)
;; (let ((bootstrap-file
;;        (expand-file-name
;;         "straight/repos/straight.el/bootstrap.el"
;;         (or (bound-and-true-p straight-base-dir)
;;             user-emacs-directory)))
;;       (bootstrap-version 7))
;;   (unless (file-exists-p bootstrap-file)
;;     (with-current-buffer
;;         (url-retrieve-synchronously
;;          "https://raw.githubusercontent.com/radian-software/straight.el/refs/heads/main/install.el"
;;          'silent 'inhibit-cookies)
;;       (goto-char (point-max))
;;       (eval-print-last-sexp)))
;;   (load bootstrap-file nil 'nomessage))

;; (straight-use-package
;;  '(gptel-autocomplete :type git :host github :repo "JDNdeveloper/gptel-autocomplete"))
