;; C++ style
(defun c++-mode-hooks()
  (font-lock-add-keywords
    nil '(
      ("\\<\\(alignof\\|alignas\\|constexpr\\|decltype\\|noexcept\\|nullptr\\|static_assert\\|thread_local\\|override\\|final\\)\\>" . 'font-lock-keyword-face)
      )))

(defadvice c-lineup-arglist (around my activate)
  "Improve indentation of continued C++11 lambda function opened as argument."
  (setq ad-return-value
        (if (and (equal major-mode 'c++-mode)
                 (ignore-errors
                   (save-excursion
                     (goto-char (c-langelem-pos langelem))
                     ;; Detect "[...](" or "[...]{". preceded by "," or "(",
                     ;;   and with unclosed brace.
                     (looking-at ".*[(,][ \t]*\\[[^]]*\\][ \t]*[({][^}]*$"))))
            0                           ; no additional indent
          ad-do-it)))                   ; default behavior

;(fa-config-default)
(add-hook 'c++-mode-hook
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
            'c++-mode-hooks
            ))

(setq irony_bin (if (string= window-system "w32") "irony-server.exe" "irony-server"))
(if (file-exists-p (concat "~/.emacs.d/irony/bin/" irony_bin))
    (progn
      (require 'irony)
      (require 'company-irony)
      (eval-after-load "irony"
        '(progn
           (custom-set-variables '(irony-additional-clang-options '("-std=c++14 -fopenmp")))
           (add-to-list 'company-backends 'company-irony)
           (add-hook 'irony-mode-hook 'irony-cdb-autosetup-compile-options)
           (add-hook 'c-mode-common-hook 'irony-mode)
           ))
      )
  (setq company-backends (delete 'company-clang company-backends))
  (add-to-list 'company-backends 'company-irony)
  )

;; (require 'flycheck)
;; (flycheck-define-checker c/c++
;;   "A C/C++ checker using g++."
;;   :command ("g++" "-Wall" "-Wextra" source)
;;   :error-patterns  ((error line-start
;;                            (file-name) ":" line ":" column ":" " エラー: " (message)
;;                            line-end)
;;                     (warning line-start
;;                            (file-name) ":" line ":" column ":" " 警告: " (message)
;;                            line-end))
;;   :modes (c-mode c++-mode))

;; テンプレート
(require 'autoinsert)
(setq auto-insert-directory "~/Documents/Programming/C++")
(setq auto-insert-alist
      (append '( ("\\.cpp$" . "template.cpp")
                 ) auto-insert-alist))

(require 'rtags)
(cmake-ide-setup)
