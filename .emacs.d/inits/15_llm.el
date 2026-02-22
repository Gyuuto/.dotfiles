(use-package gptel
  :ensure t
  :config

  (when (eq window-system 'w32)
    (setq gptel-use-curl nil))

  (setq
   gptel-model 'gemma3:4b
   gptel-backend (gptel-make-ollama "chat"
                   :host ""
                   :stream t
                   :models '()
                   :request-params '(:options (:num_ctx 16384))))

  (gptel-make-ollama "coder"
    :host ""
    :stream t
    :models '()
    :request-params '(:options (:num_ctx 16384)))

  (global-set-key (kbd "C-c g") 'gptel-menu)
  (global-set-key (kbd "C-c RET") 'gptel-send)
  (global-set-key (kbd "C-c r") 'gptel-rewrite)

  ;; ;; add-on
  ;; (require 'gptel-autocomplete)

  ;; (setq gptel-autocomplete-before-context-lines 100)
  ;; (setq gptel-autocomplete-after-context-lines 20)
  ;; (setq gptel-autocomplete-temperature 0.1)
)
