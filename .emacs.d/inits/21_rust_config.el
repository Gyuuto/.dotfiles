;;; path
(add-to-list 'exec-path (expand-file-name "'~/.cargo/bin'"))

(eval-after-load "rust-mode"
  '(setq-default rust-format-on-save t))
(add-hook 'rust-mode-hook
	  (lambda () (racer-mode) (flycheck-rust-setup))
	  )

(add-hook 'rust-mode-hook #'racer-mode)
(add-hook 'racer-mode-hook  #'eldoc-mode)

;; (add-hook 'racer-mode-hook #'company-mode)

(add-hook 'racer-mode-hook
	  (lambda ()
	    (company-mode)
	    (set (make-variable-buffer-local 'company-idle-delay) 0.1)
	    (set (make-variable-buffer-local 'company-minimum-prefix-length) 0)
	    )
	  )

;; テンプレート
(require 'autoinsert)
(setq auto-insert-directory "~/Documents/Programming/Rust")
(setq auto-insert-alist
      (append '( ("\\.rs$" . "template.rs")
                 ) auto-insert-alist))
