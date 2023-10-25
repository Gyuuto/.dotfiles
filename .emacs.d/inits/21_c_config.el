;; C style
(add-hook 'c-mode-hook
          (lambda()
            (c-set-style "stroustrup")
            (c-set-offset 'inline-open 0)
            (c-set-offset 'topmost-intro 0)
            (c-set-offset 'defun-block-intro '+)
            (c-set-offset 'statement 0)
            (c-set-offset 'statement-block-intro '+)
            (c-toggle-hungry-state 1)
            (setq tab-width 4)
            (setq c-basic-offset tab-width)
            ))

;; using clang in smart compile
(add-to-list 'smart-compile-alist
             '("\\.c$" . "gcc -O2 -Wall -o %n %f -std=c17")
             ;; '("\\.c$" . "clang -O2 -Wall -o %n %f -lstdc++ -std=c17")
             )

;; (require 'auto-complete-c-headers)
;; (add-hook 'c-mode-hook '(setq ac-sources (append ac-sources '(ac-source-c-headers))))
;(define-key c-mode-map [(tab)] 'company-complete)
(add-to-list 'company-backends 'company-c-headers)

(require 'eglot)
(add-to-list 'eglot-server-programs
             '(c-mode . ("ccls" :initializationOptions
                         (:capabilities
                          (:documentOnTypeFormattingProvider (:firstTriggerCharacter "")) ; disable auto formatting
                          ))))
(eval-after-load 'ccls
  '(progn
     (add-hook 'c-mode-common-hook 'eglot-ensure)
     )
  )

(require 'flycheck)
(flycheck-define-checker c/c++
  "A C/C++ checker using g++."
  :command ("g++" "-Wall" "-Wextra" source)
  :error-patterns  ((error line-start
                           (file-name) ":" line ":" column ":" " エラー: " (message)
                           line-end)
                    (warning line-start
                           (file-name) ":" line ":" column ":" " 警告: " (message)
                           line-end))
  :modes (c-mode))
