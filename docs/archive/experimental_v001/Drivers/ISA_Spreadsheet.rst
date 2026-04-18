pccx ISA Spreadsheet View
==========================

This page displays the HTML spreadsheet outline of the NPU ISA
Architecture exported directly from Google Sheets. For a more highly
detailed specification parameter definition, please navigate to the
`ISA Specification <ISA.html>`__ page.

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
