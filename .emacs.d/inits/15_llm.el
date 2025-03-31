(use-package ellama
  :ensure t
  :bind ("C-c g" . ellama-transient-main-menu)
  :init

  (require 'llm-ollama)

  (setopt ellama-language "Japanese")
  (setopt ellama-naming-scheme 'ellama-generate-name-by-llm)

  ;; set provider
  (setopt ellama-provider
          (make-llm-ollama
           :host ""
           :port 11434
           :chat-model "gemma3:4b"
           :embedding-model "gemma3:4b"
           )
          )
  ;; (setopt ellama-summarization-provider
  ;;         )
  ;; (setopt ellama-coding-provider
  ;;         )
  ;; (setopt ellama-naming-provider
  ;;         )
  ;; (setopt ellama-translation-provider
  ;;         )

  ;; customize display
  (push '("ellama.*\.org" :regexp t :height 0.5) popwin:special-display-config)

  ;; ask selected region in Japanese
  (defun ellama-translate-selection ()
    (interactive)
    (let
        ((text (if (region-active-p)
		           (buffer-substring-no-properties (region-beginning) (region-end))
		         (buffer-substring-no-properties (point-min) (point-max)))))
      (ellama-instant (format "What is %s?" text)
                      :system "Answer in Japanese")))

  ;; add a function define of selection sentence
  (defun ellama-define-selection ()
    "Find definition fo selection."
    (interactive)
    (let
        ((text (if (region-active-p)
		           (buffer-substring-no-properties (region-beginning) (region-end))
		         (buffer-substring-no-properties (point-min) (point-max)))))
      (ellama-instant (format ellama-define-word-prompt-template text))))

  ;; override summarize function as asnwering in Japanese
  (defun ellama-summarize ()
    "Summarize selected region or current buffer."
    (interactive)
    (let ((text (if (region-active-p)
		            (buffer-substring-no-properties (region-beginning) (region-end))
		          (buffer-substring-no-properties (point-min) (point-max)))))
      (ellama-instant text
		              :system
		              (format "%s. Also answer in Japanese." ellama-summarize-prompt-template)
		              :provider (or ellama-summarization-provider
				                    ellama-provider
				                    (ellama-get-first-ollama-chat-model)))))
  )
