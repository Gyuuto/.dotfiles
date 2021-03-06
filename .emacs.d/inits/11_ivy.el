(require 'ivy)
(ivy-mode 1)

;; M-o を ivy-hydra-read-action に割り当てる．
(when (require 'ivy-hydra nil t)
  (setq ivy-read-action-function #'ivy-hydra-read-action))

;; `ivy-switch-buffer' (C-x b) のリストに recent files と bookmark を含める．
(setq ivy-use-virtual-buffers t)

;; ミニバッファでコマンド発行を認める
(when (setq enable-recursive-minibuffers t)
  (minibuffer-depth-indicate-mode 1)) ;; 何回層入ったかプロンプトに表示．

;; プロンプトの表示が長い時に折り返す（選択候補も折り返される）
(setq ivy-truncate-lines nil)

;; set ivy buffer height
(setq ivy-height 30)

;; リスト先頭で `C-p' するとき，リストの最後に移動する
(setq ivy-wrap t)

(require 'swiper)
(global-set-key "\C-x/" 'swiper)

(require 'counsel)
(counsel-mode 1)

;; M-x history
(when (require 'smex nil t)
  (setq smex-history-length 35)
  (setq smex-completion-method 'ivy))

(defun ivy--sort-by-len (name candidates)
  "Sort CANDIDATES based on similarity of their length with NAME."
  (let ((name-len (length name))
        (candidates-count (length candidates)))
    (if (< 500 candidates-count)
        candidates
      (seq-sort-by #'length
                   (lambda (a b)
                     (< (abs (- name-len a))
                        (abs (- name-len b))))
                   candidates))))
(setf (alist-get 'counsel-M-x ivy-sort-matches-functions-alist) #'ivy--sort-by-len)

(with-eval-after-load "magit"
  (setq magit-completing-read-function 'ivy-completing-read))

(define-key global-map (kbd "M-x") 'counsel-M-x)
(define-key global-map (kbd "C-x C-f") 'counsel-find-file)
(define-key global-map (kbd "C-x C-r") 'counsel-recentf)
(define-key global-map (kbd "M-y")     'counsel-yank-pop)
(define-key global-map (kbd "C-c i")   'counsel-imenu)
(define-key global-map (kbd "C-x b")   'counsel-switch-buffer)
(define-key counsel-mode-map (kbd "C-h") 'delete-backward-char)
(global-set-key (kbd "C-c h") 'counsel-minibuffer-history)
(global-set-key (kbd "C-x C-x") 'counsel-mark-ring)
