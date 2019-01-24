(when (require 'flycheck nil 'noerror)
  (custom-set-variables
   ;; エラーをポップアップで表示
   '(flycheck-display-errors-function
     (lambda (errors)
       (let ((messages (mapcar #'flycheck-error-message errors)))
         (popup-tip (mapconcat 'identity messages "\n")))))
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

;; (with-eval-after-load 'rust-mode
;;   (add-hook 'flycheck-mode-hook #'flycheck-rust-setup))
