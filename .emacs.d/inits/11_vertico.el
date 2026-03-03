(require 'vertico)

;; print completion candidates at most 20 lines
(setq vertico-count 20)

(with-eval-after-load 'vertico
  (vertico-mode)
  (marginalia-mode)
  (savehist-mode 1)

  (setq completion-ignore-case t)
  (setq vertico-resize t)

  (require 'vertico-directory)
  (define-key vertico-map (kbd "DEL") #'vertico-directory-delete-char)
  (define-key vertico-map (kbd "M-DEL") #'vertico-directory-up)
  )

(require 'orderless)
(with-eval-after-load 'orderless
  (setq completion-styles '(orderless basic substring partial-completion flex))
  (setq completion-category-defaults nil)
  (setq completion-category-overrides
        '((file (styles basic partial-completion))
          (command (styles basic))
          (variable (styles basic))
          (symbol (styles basic))))
  )

(require 'consult)
(with-eval-after-load 'consult
  (setq completion-in-region-function #'consult-completion-in-region)
  (with-eval-after-load 'embark
    (require 'embark-consult)))

;; (global-set-key (kbd "C-x C-f") 'consult-find)
(global-set-key (kbd "C-x b") 'consult-buffer)
(global-set-key (kbd "M-y") 'consult-yank-from-kill-ring)
(global-set-key (kbd "M-g g") 'consult-goto-line)
(global-set-key (kbd "C-x C-x") 'consult-line)
(global-set-key (kbd "C-x C-r") 'consult-grep)
