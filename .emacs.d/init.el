(setq system_path "~")

;; set default directory
(setq default-directory (concat system_path "/"))

;; read init.el of each host
(setq init_host (concat system_path "/.dotfiles/.emacs.d/init_" (system-name) ".el"))
(if (file-exists-p init_host)
    (load-file init_host))


;; add package (melpa, maramalade)
(require 'package)
(setq pakcage-user-dir (concat system_path "/.emacs.d/elisp/elpa"))
(add-to-list 'package-archives '("melpa" . "http://melpa.milkbox.net/packages/") t)
(add-to-list 'package-archives '("marmalade" . "https://marmalade-repo.org/packages/"))
(package-initialize)


;; init-loader
(require 'init-loader)
(setq init-loader-show-log-after-init 'error-only)
(init-loader-load (concat system_path "/.dotfiles/.emacs.d/inits"))
