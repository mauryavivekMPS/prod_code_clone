// App.js
import React from 'react';
import ReactDOM from 'react-dom';
import PendingFiles from './src/Pending-Files';

const PendingFilesElem = document.getElementById('ivweb-pending-files');
if (PendingFilesElem) {
  ReactDOM.render(
    <PendingFiles></PendingFiles>,
    PendingFilesElem
  )
}
