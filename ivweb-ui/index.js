// App.js
import React from 'react';
import ReactDOM from 'react-dom';
import PendingFiles from './src/Pending-Files';

const components = [
  {
    ref: PendingFiles,
    className: '.ivweb-pending-files',
    propNames: [ 'ivetlProductId', 'ivetlPipelineId', 'ivetlPublisherId',
    'ivetlUploadUrl', 'ivetlDeleteUrl', 'ivetlPendingFilesUrl',
    'ivetlPendingFiles', 'ivetlIsDemo', 'ivetlCsrfToken' ]
  }
]

components.forEach(component => {
  document.querySelectorAll(component.className)
    .forEach(domContainer => {
      let props = {};
      console.log('dataset:');
      console.log(domContainer.dataset);
      component.propNames.forEach(function initProp(elem) {
        if (domContainer.dataset &&
        typeof domContainer.dataset[elem] !== 'undefined') {
          props[elem] = domContainer.dataset[elem]
        }
      });
      console.log('props:');
      console.log(props);
      ReactDOM.render(
        React.createElement(
          component.ref,
          props
        ),
        domContainer
      )
    });
});
