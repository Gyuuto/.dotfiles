(use-package gptel
  :ensure t
  :config

  (when (eq window-system 'w32)
    (setq gptel-use-curl nil))

  (let* ((server my/llm-server-latest-light-chat))
    (setq
     gptel-model (my/llm-server-model server)
     gptel-backend (gptel-make-openai "latest-light-chat"
                     :host (my/llm-server-host server)
                     :stream t
                     :models (my/llm-server-model server)
                     :request-params '(:options (:num_ctx 16384)))))
                     :protocol "http"
                     :endpoint "/v1/chat/completions"

  (let* ((server my/llm-server-latest-chat))
    (gptel-make-openai "latest-chat"
      :host (my/llm-server-host server)
      :stream t
      :models (my/llm-server-model server)
      :protocol "http"
      :endpoint "/v1/chat/completions"
      :request-params '(:options (:num_ctx 8192))))

  (let* ((server my/llm-server-latest-light-coder))
    (gptel-make-openai "latest-light-coder"
      :host (my/llm-server-host server)
      :stream t
      :models (my/llm-server-model server)
      :request-params '(:options (:num_ctx 16384))))
      :protocol "http"
      :endpoint "/v1/chat/completions"

  (let* ((server my/llm-server-latest-coder))
    (gptel-make-ollama "latest-coder"
      :host (my/llm-server-host server)
      :stream t
      :models (my/llm-server-model server)
      :protocol "http"
      :endpoint "/v1/chat/completions"
      :request-params '(:options (:num_ctx 8192))))

  (setq gptel-directives
        '((default . "あなたはEmacs上で動作する優秀で役立つAIアシスタントです。ユーザーの質問や指示に対して、簡潔かつ的確に答えてください。出力は読みやすいMarkdown形式で行い、不要な前置きや結論の繰り返しは避けてください。")
          (programming . "あなたは熟練したシニアソフトウェアエンジニアです。コードの作成、リファクタリング、デバッグ、または技術的な説明を行ってください。挨拶や不要な会話は一切省き、最適化されたセキュアなコードと、必要最小限の的確な解説のみを提供してください。コードは必ずMarkdownのコードブロック（言語名指定あり）で記述してください。")
          (writing . "あなたはプロフェッショナルなライター兼編集者です。提供されたテキストを推敲し、より自然で読みやすく、説得力のある文章に改善してください。誤字脱字や文法エラーを修正し、文脈に応じた適切なトーン（フォーマル、カジュアルなど）を維持してください。大幅な変更を加えた場合は、その理由も簡潔に添えてください。")
          (chat . "あなたは創造的で親しみやすい対話パートナーです。ユーザーのアイデアの壁打ち相手として、柔軟な発想で会話を広げてください。返答は長すぎないようにテンポ良く行い、時には質問を投げかけてユーザーの思考を深める手助けをしてください。")
          (consider . "あなたは冷静で分析力に優れた戦略コンサルタントです。提示された課題やテーマについて、直感的な結論を急がず、多角的な視点から深く考察してください。前提条件の確認、メリットとデメリットの比較、想定されるリスク、および代替案を論理的かつ構造的に整理し、ステップバイステップで思考プロセスを提示してください。")))

  (global-set-key (kbd "C-c g") 'gptel-menu)
  (global-set-key (kbd "C-c RET") 'gptel-send)
  (global-set-key (kbd "C-c r") 'gptel-rewrite)

  ;; ;; add-on
  ;; (require 'gptel-autocomplete)

  ;; (setq gptel-autocomplete-before-context-lines 100)
  ;; (setq gptel-autocomplete-after-context-lines 20)
  ;; (setq gptel-autocomplete-temperature 0.1)
)
