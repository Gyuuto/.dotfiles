;; mac コマンドキーをメタキーとして使う
(setq ns-command-modifier (quote meta))
(setq ns-alternate-modifier (quote super))
(setq mac-pass-control-to-system nil)
(setq mac-pass-command-to-system nil)
(setq mac-pass-option-to-system nil)

;; undo
(global-set-key "\C-z" 'undo)
(global-set-key (kbd "C-_") nil)

;; change keymap of BS to C-h
(keyboard-translate ?\C-h ?\C-?)
(global-unset-key "\C-h")

;; uncomment lines
(define-key global-map "\C-c\C-v" 'uncomment-region)

;; compile command
(define-key mode-specific-map "c" 'compile)

(require 'smart-compile)
(define-key mode-specific-map "c" 'smart-compile)

;; (require 'shell-command)
;; (shell-command-completion-mode)
;; (define-key mode-specific-map "\C-z" 'shell-command)

;; move other buffer
(defun other-window-or-split ()
  (interactive)
  (other-window 1))

(global-set-key (kbd "C-q") 'other-window-or-split)

;; magit shortcut
(global-set-key (kbd "C-x g") 'magit-status)

;; ;; redefine xref-find-apropos
;; (global-unset-key (kbd "C-M-."))
;; (global-set-key (kbd "C-M-_") 'xref-find-apropos)

;; define ace-window
(global-set-key (kbd "C-q") 'ace-window)
