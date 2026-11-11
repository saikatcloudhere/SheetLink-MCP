/**
 * SheetLink-MCP: Google Apps Script Backend Engine
 * Author: Saikat (https://github.com/saikatcloudhere)
 * Project: SheetLink-MCP (https://github.com/saikatcloudhere/SheetLink-MCP)
 *
 * Instructions:
 * 1. Open your target Google Sheet (https://sheets.new).
 * 2. Click Extensions > Apps Script in the top menu.
 * 3. Replace all existing text with this code.
 * 4. Save, select setupSheetLink, and click Run. Approve permissions if asked.
 * 5. Click Deploy > New deployment and select Web app.
 * 6. Set Execute as to Me and Who has access to Anyone, then copy the Web App URL.
 */

function setupSheetLink() {
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  if (!spreadsheet) {
    throw new Error("Open Apps Script from your Google Sheet and run setupSheetLink in the editor.");
  }
  PropertiesService.getScriptProperties().setProperty("SHEETLINK_SPREADSHEET_ID", spreadsheet.getId());
}

function doGet(e) {
  return handleRequest(e, "GET");
}

function doPost(e) {
  return handleRequest(e, "POST");
}

function handleRequest(e, method) {
  try {
    var spreadsheetId = PropertiesService.getScriptProperties().getProperty("SHEETLINK_SPREADSHEET_ID");
    if (!spreadsheetId) {
      return jsonResponse({
        status: "error",
        message: "Run setupSheetLink once from the Apps Script editor linked to your Google Sheet."
      });
    }
    var ss = SpreadsheetApp.openById(spreadsheetId);
    var action = "read";
    var payload = {};

    // 1. Parse parameters and payload
    if (method === "POST" && e && e.postData && e.postData.contents) {
      try {
        payload = JSON.parse(e.postData.contents);
        action = payload.action || "append_row";
      } catch (parseErr) {
        return jsonResponse({
          status: "error",
          message: "Malformed JSON payload: " + parseErr.toString()
        });
      }
    } else if (e && e.parameter && e.parameter.action) {
      action = e.parameter.action;
    }

    // 2. Select target worksheet tab (defaults to the first tab if not specified)
    var targetSheetName = payload.sheet_name || (e && e.parameter ? e.parameter.sheet_name : null);
    var sheet;
    if (targetSheetName) {
      sheet = ss.getSheetByName(targetSheetName);
      if (!sheet) {
        return jsonResponse({
          status: "error",
          message: "Worksheet tab '" + targetSheetName + "' not found in spreadsheet."
        });
      }
    } else {
      sheet = ss.getSheets()[0];
    }

    // ACTION 1: Read all records
    if (action === "read" || method === "GET") {
      var dataRange = sheet.getDataRange();
      var data = dataRange.getValues();

      // Clean up completely empty sheets representation
      if (data.length === 1 && data[0].length === 1 && data[0][0] === "") {
        data = [];
      }

      return jsonResponse({
        status: "success",
        sheet_name: sheet.getName(),
        total_rows: data.length,
        data: data
      });
    }

    // ACTION 2: Append new row
    if (action === "append_row") {
      var rowData = payload.row_data;
      if (!Array.isArray(rowData)) {
        return jsonResponse({
          status: "error",
          message: "Missing or invalid 'row_data'. Expected an array of cell values."
        });
      }

      sheet.appendRow(rowData);
      SpreadsheetApp.flush();

      return jsonResponse({
        status: "success",
        sheet_name: sheet.getName(),
        message: "Row appended successfully",
        row_count: sheet.getLastRow()
      });
    }

    // ACTION 3: Search and update cell by value
    if (action === "update_cell") {
      var searchText = payload.search_text;
      var columnIndex = parseInt(payload.column_index, 10);
      var newValue = payload.new_value;

      if (!searchText || isNaN(columnIndex) || columnIndex < 1 || newValue === undefined) {
        return jsonResponse({
          status: "error",
          message: "Invalid parameters. 'search_text', 'column_index' (positive integer), and 'new_value' are required."
        });
      }

      var textFinder = sheet.createTextFinder(String(searchText));
      var foundCell = textFinder.findNext();
      if (!foundCell) {
        return jsonResponse({
          status: "error",
          message: "Search term '" + searchText + "' not found in worksheet '" + sheet.getName() + "'."
        });
      }

      var targetRow = foundCell.getRow();

      // Dynamically expand columns if columnIndex exceeds current sheet bounds
      var maxCols = sheet.getMaxColumns();
      if (columnIndex > maxCols) {
        sheet.insertColumnsAfter(maxCols, columnIndex - maxCols);
      }

      sheet.getRange(targetRow, columnIndex).setValue(newValue);
      SpreadsheetApp.flush();

      return jsonResponse({
        status: "success",
        sheet_name: sheet.getName(),
        message: "Updated Row " + targetRow + ", Column " + columnIndex + " to '" + newValue + "'."
      });
    }

    return jsonResponse({
      status: "error",
      message: "Unrecognized action: " + action
    });

  } catch (err) {
    return jsonResponse({
      status: "error",
      message: "Server script error: " + err.toString()
    });
  }
}

function jsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
