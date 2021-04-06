// App.js
import React from 'react';
import ReactDOM from 'react-dom';
import PendingFiles from './src/Pending-Files';

const components = [
  {
    ref: PendingFiles,
    className: '.ivweb-pending-files',
    propNames: [ 'ivetlProductId', 'ivetlPipelineId', 'ivetlPublisherId',
    'ivetlUploadUrl', 'ivetlDeleteUrl', 'ivetlRunPipelineUrl', 'ivetlLogoUrl',
    'ivetlPendingFilesUrl', 'ivetlPendingFiles', 'ivetlIsDemo',
    'ivetlCsrfToken', 'ivetlLegacyUploads']
  }
]

components.forEach(component => {
  document.querySelectorAll(component.className)
    .forEach(domContainer => {
      let props = {};
      component.propNames.forEach(function initProp(elem) {
        if (domContainer.dataset &&
        typeof domContainer.dataset[elem] !== 'undefined') {
          props[elem] = domContainer.dataset[elem]
        }
      });
      ReactDOM.render(
        React.createElement(
          component.ref,
          props
        ),
        domContainer
      )
    });
});
