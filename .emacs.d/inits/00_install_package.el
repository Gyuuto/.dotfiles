(require 'cl)

(defvar installing-package-list
  '(
    ;; ここに使っているパッケージを書く。
    smart-compile
    shell-command
    exec-path-from-shell
    auto-complete
    ansi-color
    anything
    popwin
    helm
    helm-git-grep
    helm-gtags
    helm-ls-git
    matlab-mode
    yatex
    magit
    ))

(let ((not-installed (loop for x in installing-package-list
			   when (not (package-installed-p x))
			   collect x)))
  (when not-installed
    (package-refresh-contents)
    (dolist (pkg not-installed)
      (package-install pkg))))
