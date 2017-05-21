// Main File with Javascript functionality

  //Submit data when enter key is pressed
  $('#input_frase_arg').keydown(function(e) {
      var text = $('#input_frase_arg').val();
        if (e.which == 13 && text.length > 0) { //catch Enter key
          //POST request to API to create a new visitor entry in the database
            $.ajax({
      method: "POST",
      url: "./api/analyze-text",
      contentType: "application/json",
      data: JSON.stringify({text: text })
    })
            .done(function(data) {
                $('#response').html(data);
                $('#input_frase').hide();
                $('#input_imagen_all').hide();
                //getNames();
            });
        }
    });

    //Retrieve all the visitors from the database
    //function getNames(){
    //  $.get("./api/visitors")
    //      .done(function(data) {
    //          if(data.length > 0) {
    //            $('#databaseNames').html("Database contents: " + JSON.stringify(data));
    //          }
    //      });
    //  }

      //Call getNames on page load.
    //  getNames();