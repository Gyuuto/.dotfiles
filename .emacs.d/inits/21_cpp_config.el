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
            (c-set-offset 'inlambda 0)
            (c-set-offset 'block-open 0)
            (c-set-offset 'innamespace 0)
            (c-toggle-hungry-state 1)
            (setq tab-width 4)
            (setq c-basic-offset tab-width)
            (yas-minor-mode)
            'c++-mode-hooks
            ))

;; using clang in smart compile
(add-to-list 'smart-compile-alist
             '("\\.cpp$" . "clang++ -O2 -Wall -o %n %f -lstdc++ -std=c++17"))

;;; config eglot with clangd
(with-eval-after-load 'eglot
  (add-to-list 'eglot-server-programs
               '((c++-mode) "clangd"))
  (add-hook 'c-mode-common-hook 'eglot-ensure)
  )

(use-package eglot-inactive-regions
  :custom
  (eglot-inactive-region-style 'darken-foreground)
  (eglot-inactive-region-opacity 0.4)
  :config
  (eglot-inactive-regions-mode 1)
  )

;; (require 'lsp-mode)
;; (eval-after-load 'lsp-mode
;;   '(progn
;;      (add-hook 'lsp-mode-hook 'lsp-headerline-breadcrumb-mode)

;;      (setq lsp-headerline-breadcrumb-segments '(symbols))
;;      (setq lsp-enable-on-type-formatting nil)
;;      (setq gc-cons-threshold 12800000)
;;      (setq read-process-output-max (* 1024 1024))
;;      ))
;; (eval-after-load 'ccls
;;   '(progn
;;      (add-hook 'c-mode-common-hook 'lsp)
;;      )
;;   )

;; (require 'lsp-ui)
;; (eval-after-load 'lsp-ui
;;   '(progn
;;      (add-hook 'lsp-mode-hook 'lsp-ui-mode)

;;      (define-key lsp-ui-mode-map (kbd "C-_") 'lsp-ui-sideline-toggle-symbols-info) ; only run via terminal?
;;      (define-key lsp-ui-mode-map (kbd "C-?") 'lsp-ui-sideline-toggle-symbols-info)
;;      ))

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
  :modes (c++-mode))

;; テンプレート
(require 'autoinsert)
(setq auto-insert-directory "~/Documents/Programming/C++")
(setq auto-insert-alist
      (append '( ("\\.cpp$" . "template.cpp")
                 ) auto-insert-alist))

;; (require 'rtags)
;; (cmake-ide-setup)


;; eglot customization
;; (with-eval-after-load 'eglot
;;   (progn
;;     ;; clangd
;;     (cl-defmethod eglot-clangd-client-capabilities :around (server)
;;       (let ((base (cl-call-next-method)))
;;         (when (cl-find "clangd" (process-command
;;                                  (jsonrpc--process server))
;;                        :test #'string-match)
;;           (setf (cl-getf (cl-getf base :textDocument)
;;                          :inactiveRegionsCapabilities)
;;                 '(:inactiveRegions t)))
;;         base))

;;     (defvar-local eglot-clangd-inactive-range-overlays '())
;;     (cl-defmethod eglot-handle-notification
;;       (_server (_method (eql textDocument/inactiveRegions)) &rest _params)
;;       (if-let* ((path (expand-file-name (eglot--uri-to-path (cl-getf _params :uri))))
;;                 (buffer (find-buffer-visiting path))
;;                 (regions (cl-getf _params :inactiveRegions)))
;;           (with-current-buffer buffer
;;             (mapc #'delete-overlay eglot-clangd-inactive-range-overlays)
;;             (cl-loop
;;              for r across regions
;;              for (beg . end) = (eglot--range-region r)
;;              for ov = (make-overlay beg end)
;;              do
;;              (overlay-put ov 'face 'shadow)
;;              (push ov eglot-clangd-inactive-range-overlays)))
;;         )
;;       )

;; ;;     (defun eglot-ccls-inheritance-hierarchy (&optional derived)
;; ;;       "Show inheritance hierarchy for the thing at point.
;; ;; If DERIVED is non-nil (interactively, with prefix argument), show
;; ;; the children of class at point."
;; ;;       (interactive "P")
;; ;;       (if-let* ((res (jsonrpc-request
;; ;;                       (eglot--current-server-or-lose)
;; ;;                       :$ccls/inheritance
;; ;;                       (append (eglot--TextDocumentPositionParams)
;; ;;                               `(:derived ,(if derived t :json-false))
;; ;;                               '(:levels 100) '(:hierarchy t))))
;; ;;                 (tree (list (cons 0 res))))
;; ;;           (with-help-window "*ccls inheritance*"
;; ;;             (with-current-buffer standard-output
;; ;;               (while tree
;; ;;                 (pcase-let ((`(,depth . ,node) (pop tree)))
;; ;;                   (cl-destructuring-bind (&key uri range) (plist-get node :location)
;; ;;                     (insert (make-string depth ?\ ) (plist-get node :name) "\n")
;; ;;                     (make-text-button (+ (point-at-bol 0) depth) (point-at-eol 0)
;; ;;                                       'action (lambda (_arg)
;; ;;                                                 (interactive)
;; ;;                                                 (find-file (eglot--uri-to-path uri))
;; ;;                                                 (goto-char (car (eglot--range-region range)))))
;; ;;                     (cl-loop for child across (plist-get node :children)
;; ;;                              do (push (cons (1+ depth) child) tree)))))))
;; ;;         (eglot--error "Hierarchy unavailable")))

;; ;;     (global-set-key (kbd "C-c _") 'eglot-ccls-inheritance-hierarchy)
;;     ))
