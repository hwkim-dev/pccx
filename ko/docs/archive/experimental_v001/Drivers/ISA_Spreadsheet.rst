pccx ISA 스프레드시트 뷰
==========================

이 페이지는 Google Sheets 에서 직접 내보낸 NPU ISA 아키텍처의 HTML
스프레드시트 개요를 표시합니다. 더 상세한 사양 파라미터 정의는
:doc:`ISA` 페이지를 참고하세요.

.. raw:: html

   <style>
   /* Make this page's main content area stretch so the iframe fills the screen */
   .isa-sheet-wrap {
     position: relative;
     width: 100%;
     height: calc(100vh - 140px);
     min-height: 480px;
     border-radius: 8px;
     overflow: hidden;
     box-shadow: 0 2px 12px rgba(0,0,0,0.10);
   }
   .isa-sheet-wrap iframe {
     position: absolute;
     inset: 0;
     width: 100%;
     height: 100%;
     border: none;
   }
   </style>

   <div class="isa-sheet-wrap">
     <iframe
       src="../../../../_static/ISA_Instruction_set_architecture.html"
       title="pccx ISA Spreadsheet">
     </iframe>
   </div>
