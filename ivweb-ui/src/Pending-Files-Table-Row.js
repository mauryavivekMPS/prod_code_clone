import React, { Component } from 'react';

function PendingFilesTableRow (props) {
  let file = props.file;
  const validationErrors = file.validation_errors &&
    file.validation_errors.length > 0;
  const deleteFile = () => {
    if (props.cb && typeof props.cb === 'function') {
      props.cb(file);
    }
    else {
      console.log('No callback defined for PendingFilesTableRow');
    }
  };

  const statusIcon = validationErrors
    ? (<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#900" className="bi bi-exclamation-circle-fill" viewBox="0 0 16 16">
         <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM8 4a.905.905 0 0 0-.9.995l.35 3.507a.552.552 0 0 0 1.1 0l.35-3.507A.905.905 0 0 0 8 4zm.002 6a1 1 0 1 0 0 2 1 1 0 0 0 0-2z"/>
       </svg>)
    : (<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#259" className="bi bi-check-circle-fill" viewBox="0 0 16 16">
         <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
       </svg>);

  const deleteCol = !props.readOnly && !validationErrors
    ? (
        <a className="btn btn-default submit-button delete-file-button" onClick={deleteFile}>
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#444" className="bi bi-trash-fill" viewBox="0 0 16 16">
            <path d="M2.5 1a1 1 0 0 0-1 1v1a1 1 0 0 0 1 1H3v9a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V4h.5a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H10a1 1 0 0 0-1-1H7a1 1 0 0 0-1 1H2.5zm3 4a.5.5 0 0 1 .5.5v7a.5.5 0 0 1-1 0v-7a.5.5 0 0 1 .5-.5zM8 5a.5.5 0 0 1 .5.5v7a.5.5 0 0 1-1 0v-7A.5.5 0 0 1 8 5zm3 .5v7a.5.5 0 0 1-1 0v-7a.5.5 0 0 1 1 0z"/>
          </svg>
        </a>
      )
    : ('');

  const fileStatus = validationErrors
    ? (<a href="#" className="show-errors-link">
      Errors: { file.validation_errors.length }
      </a>)
    : (<span className="success-message">Validated</span>);

  return (
    <tr className={`file-row file-row-${file.file_id}`} key={`file-row-${file.file_id}`}>
      <td className="status-icon-col">{ statusIcon }</td>
      <td className="text-only-col">{ file.file_name }</td>
      <td className="text-only-col line-count-col">{ file.line_count }</td>
      <td className="text-only-col file-size-col">{ file.file_size }</td>
      <td className="text-only-col file-status-col">{ fileStatus }</td>
      <td className="delete-file-col">{ deleteCol }</td>
    </tr>
  )
}

function PendingFilesTableError (props) {
  const file = props.file;
  let validationErrors = false;
  let errorRows = null;
  if (file.validation_errors && file.validation_errors.length > 0) {
    validationErrors = true;
    errorRows = file.validation_errors.map((item, idx) => {
      return (<tr key={`file-${file.file_id}-line-error-${idx}`}>
            <td className="line-number-col">{ item.line_number }</td>
            <td className="message">{ item.message }</td>
        </tr>)
    })
  }

  function replaceFile(event) {
    /* todo: determine if this functionality will actually be needed.
    see more detailed comment below inline within the JSX.
    */
  }

  const inputs = props.isDemo
    ? (
      <div>
      <input type="hidden" name="file_type" value="demo" />
      <input type="hidden" name="demo_id" value="{{ demo_id }}" />
      </div>
    )
    : (
      <div>
      <input type="hidden" name="file_type" value="publisher" />
      <input type="hidden" name="publisher_id" value="{{ publisher_id }}" />
      </div>
    );

  const validationInputs = props.hasSecondLevelValidation
    ? (
      <div>
        <input type="checkbox" className="second-level-validation"
        id="id_second_level_validation_{{ file_index }}"
        name="second_level_validation" value="1" />
        { pipeline.second_level_validation_label || 'Validate all rows'}
      </div>
    )
    : (
      <div></div>
    );

  return (<tr className={`error-list-row file-row-${file.file_id}`}
      key={`error-row-${file.file_id}`}>
        <td></td>
        <td></td>
        <td colSpan="5" className="validation-error-table-col">
            <table className="table validation-error-table">
                <tbody>{ errorRows }<tr>{
                          /*
                          todo: determine if we still need to support
                          individual file replacements.
                          Current implementation uses drag/drop zone for
                          file validator.
                          wiring in a replacement may not be necessary,
                          as we are now validating client side.
                          However, for current compatiblity, we may have
                          files in the system that are error'ed out and
                          need a replacement. For initial impelmentation,
                          support should be able to direct users with
                          existing files to the legacy form.
                          Going forward, it is expected that we'll generally
                          be validating files client-side and won't have
                          this issue of un-validated, error-containging files
                          sitting on the server waiting for a fix.
                          <td>
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#222" className="bi bi-file-earmark-arrow-up-fill" viewBox="0 0 16 16">
                              <path d="M9.293 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4.707A1 1 0 0 0 13.707 4L10 .293A1 1 0 0 0 9.293 0zM9.5 3.5v-2l3 3h-2a1 1 0 0 1-1-1zM6.354 9.854a.5.5 0 0 1-.708-.708l2-2a.5.5 0 0 1 .708 0l2 2a.5.5 0 0 1-.708.708L8.5 8.707V12.5a.5.5 0 0 1-1 0V8.707L6.354 9.854z"/>
                            </svg>
                          </td>
                          <td className="upload-replacement-col">
                              This file was rejected, please fix and try again:
                              <form onSubmit={replaceFile}
                              className="inline-upload-form" method="post" encType="multipart/form-data">
                                  { props.csrf_token }
                                  <input type="hidden" name="product_id" value={ props.productId } />
                                  <input type="hidden" name="pipeline_id" value={ props.pipelineId } />
                                  { inputs }
                                  <input type="hidden" name="ui_type" value="replacement" />
                                  <div className="inline-upload-form-controls">
                                      <input className="replacement-file-picker"
                                      id={`id_file_${ file.file_id }`}
                                      name="files" type="file"
                                      ui_type="replacement" />
                                      { validationInputs }
                                  </div>
                              </form>
                          </td>
                          */
                        }</tr>
                </tbody>
            </table>
        </td>
    </tr>);
}

export { PendingFilesTableRow, PendingFilesTableError };
