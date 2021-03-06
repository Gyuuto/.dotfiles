;; yatex-modeの設定
(require 'yatex)
;; AMS-LaTeXを使う
(setq YaTeX-use-AMS-LaTeX t)
;; 漢字コードをEUCに設定
(setq YaTeX-kanji-code nil)
;; タイプセッター時のTeXをplatexに設定
(setq tex-command "platex")
;; プレビューワの設定
;;(setq dvi2-command "dvipdfmx")
;; 印刷コマンド
(setq dviprint-command-format "dvipdfmx %S")
(setq dviprint-from-format "-p %b")
(setq dviprint-to-format "-l %e")
;; section型補完の規定値
(setq section-name "section")
;; Begin ショートカットの禁止 (いきなり補完入力)
(setq YaTeX-no-begend-shortcut t)
;; 数式の色付け
(if (featurep 'hilit19)
    (hilit-translate
     forumula 'DeepPink1)
)
;; [prefix] g で相手のファイルがなかったら新規作成
(setq YaTeX-create-file-prefix-g t)
;; 数式モードの";"補完の強化
(setq YaTeX-math-sign-alist-private
      '(("q" "quad" "__")
        ("qq" "qquad" "____")
        ("ls" "varlimsup" "___\nlim")
        ("li" "varliminf" "lim\n---")
        ("il" "varinjlim" "lim\n-->")
       ;("st" "text{ s.~t. }" "s.t.")
        ("bigop" "bigoplus" "_\n(+)~")
        ("bigot" "bigotimes" "_\n(x)\n ~")
        ("pl" "varprojlim" "lim\n<--"))
)
;;数式モードの","補間
(setq YaTeX-math-funcs-list
      '(("s"	"sin"           "sin")
	("c"    "cos"           "cos") 
	("t"    "tan"           "tan")
	("hs"	"sinh"          "sinh")
	("hc"   "cosh"          "cosh")
	("ht"   "tanh"          "tanh")
	("S"	"arcsin"        "arcsin")
	("C"    "arccos"        "arccos")
	("T"    "arctan"        "arctan")
	("se"   "sec"           "sec")
	("cs"   "csc"           "csc")
	("cot"  "cot"           "cot")
	("l"    "ln"            "ln")
	("L"    "log"           "log")
	("e"    "exp"           "exp")
	("M"    "max"           "max")
	("m"    "min"           "min")
	("su"   "sup"           "sup")
	("in"   "inf"           "inf")
	("di"   "dim"           "dim")
	("de"   "det"           "det")
	("i"    "imath"         "i")
	("j"    "jmath"         "j")
	("I"    "Im"            "Im")
	("R"    "Re"            "Re")
	)
)
(setq YaTeX-math-key-list-private
      '(("," . YaTeX-math-funcs-list)
	)
)
;;
;; generated by YaTeX-generate
;;
(defun YaTeX:includegraphics ()
  (concat
   (let ((op (read-string "width: ")))
     (if (string< "" op)
	 (concat "[" op "]")
       ""))
   ))

(defun YaTeX::includegraphics (&optional argp)
  (cond
   ((equal argp 1)
    (read-file-name "include eps file: "  "" t "")
    )
   ))

;; for double quote
(setq YaTeX-use-font-lock t
      YaTeX-19-recenter-function nil)
(add-hook 'yatex-mode-hook 'turn-on-font-lock)
(add-hook 'yatex-mode-load-hook
	  (lambda ()
	    (modify-syntax-entry ?\" "w" YaTeX-mode-syntax-table)
	    )
          )
(let (elem)
  (while (setq elem (or (rassq 'tex-mode auto-mode-alist)
			(rassq 'latex-mode auto-mode-alist)
			(rassq 'bibtex-mode auto-mode-alist)))
    (setcdr elem 'yatex-mode)))
(autoload 'yatex-mode "yatex" nil t )
(add-hook 'yatex-mode-hook
	  (lambda ()
	    (local-set-key "\"" 'self-insert-command)
	    )
          )
