(when (require 'flycheck nil 'noerror)
  (custom-set-variables
   '(flycheck-display-errors-delay 0.5))
  (define-key flycheck-mode-map (kbd "C-M-f") 'flycheck-next-error)
  (define-key flycheck-mode-map (kbd "C-M-b") 'flycheck-previous-error)
  (add-hook 'c-mode-common-hook 'flycheck-mode))

(eval-after-load 'flycheck
  '(progn
     (when (locate-library "flycheck-irony")
       (flycheck-irony-setup))
     (add-hook 'flycheck-mode-hook #'flycheck-irony-setup))
  )

;; popup warning and errors
(with-eval-after-load 'flycheck
  (flycheck-popup-tip-mode))

;; (with-eval-after-load 'rust-mode
;;   (add-hook 'flycheck-mode-hook #'flycheck-rust-setup))
