(require 'cl)

(defvar installing-package-list
  '(
    ;; ここに使っているパッケージを書く。
    ;;; mode
    web-mode
    cmake-mode
    matlab-mode
    markdown-mode
    ;;; useful for programming
    smart-compile
    auto-complete
    company
    company-irony
    irony
    magit
    ;;; shell ?
    shell-command
    exec-path-from-shell
    ;;; useful for buffer
    anything
    popwin
    helm
    helm-git-grep
    helm-gtags
    helm-ls-git
    ;auto-complete-c-headers
    ;auto-complete-clang-async
    ;function-args
    ;flycheck
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
