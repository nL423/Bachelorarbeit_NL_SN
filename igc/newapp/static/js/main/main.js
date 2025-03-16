$(document).ready(function () {
  cooldown = setTimeout(() => {}, 1);

  /*
  ----------------------------------------------------------------------------- (START) NEW by Nico Lambert --------------------------------------------------------
  */
  // used to get the information, which type of search was last used - standard , simple/absolute genarlise/sepcialise search  or hierarchy equivalent search of current Tag 
  let lastSearchType = "";
  /*
  ------------------------------------------------------------------------------- (END) NEW by Nico Lambert --------------------------------------------------------
  */
  let appState = {
    _coins: [],
    latestResponse: null,
    latestCoinResult: null,
    sortedCoinResult: null,
    currentSearchType: "NumismaticObject",
    currentCoin: {
      obverse: { coin: [], keywords: [] },
      reverse: { coin: [], keywords: [] },
    },
    relationString: "",
    cursorPosition: null,
    currentPage: 1,
    resultsPerPage: 100,
    totalPages: 1,

    /**
     * Getter for _coins array.
     * @returns {Array} The current array of coins.
     *
     * @Author: Danilo Pantic
     */
    get coins() {
      return this._coins;
    },

    /**
     * Setter for _coins array, triggers state change actions.
     * @param {Array} value - The new coin array.
     *
     * @Author: Danilo Pantic
     */
    set coins(value) {
      this._coins = value;
      this.onCoinsChange();
    },

    /**
     * Adds a coin to the state and triggers updates.
     * @param {Object} coin - The coin object to add.
     *
     * @Author: Danilo Pantic
     */
    addCoin: function (coin) {
      this._coins.push(coin);
      this.onCoinsChange();
    },

    /**
     * Clears all coins from the state and triggers updates.
     *
     * @Author: Danilo Pantic
     */
    clearCoins: function () {
      this._coins = [];
      this.onCoinsChange();

      $("#searchActions .searchcoin").prop("disabled", true);
    },

    /**
     * Function to handle updates when coins change.
     *
     * @Author: Danilo Pantic
     */
    onCoinsChange: function () {
      renderCoins();
      refreshRelationString();
      regenerateQuery();
    },

    /**
     * Sets the current page and rerenders visual elements..
     * @param {number} page - The desired page number.
     *
     * @Author: Danilo Pantic
     */
    setPage: function (page) {
      this.currentPage = page;
      renderResults();
    },

    /**
     * Switches to next page (if possible) and rerenders respective results.
     *
     * @Author: Danilo Pantic
     */
    nextPage: function () {
      if (this.currentPage < this.totalPages) {
        this.currentPage++;
        this.renderCurrentPage();
      }
    },

    /**
     * Switches to previous page (if possible) and rerenders respective results.
     *
     * @Author: Danilo Pantic
     */
    previousPage: function () {
      if (this.currentPage > 1) {
        this.currentPage--;
        this.renderCurrentPage();
      }
    },

    /**
     * Renders the results of the current page based on the current page number and results per page settings.
     * This function handles sorting of the results, slicing them for the current page, grouping them according to selected criteria,
     * and finally rendering them on the webpage. It also updates the pagination controls and resets the scroll position of the results container.
     *
     * @Author: Danilo Pantic
     */
    renderCurrentPage: function () {
      sortResults();

      const start = (this.currentPage - 1) * this.resultsPerPage;
      const end = start + this.resultsPerPage;
      const currentItems = appState.sortedCoinResult.slice(start, end);
      const groupedResults = groupResults(
        currentItems,
        $("#groupSelect").val()
      );

      renderResults(groupedResults);
      updatePaginationControls();
      $("#resultBox").scrollTop(0);
    },
  };

  // Author: Mohammed Sayed Mahmod
  var editor = CodeMirror.fromTextArea($("#sparqlQuery")[0], {
    mode: "application/sparql-query",
    lineNumbers: true,
    theme: "default",
    value: "",
  });

  /**
   * Converts an item to a tag element
   * @param {Object} item - The item to convert
   * @param {string} category - The category of the item
   * @returns {jQuery} The tag element
   *
   * @Author: Danilo Pantic , UPDATE by Nico Lambert, UPDATE by Steven Nowak
   */
  function item2Tag(item, category) {
    

    let new_tag = $("<div class='tag'></div>");
    
    let iconToDisplay = null;

    /*
    ----------------------------------------------------------------------------- (START) UPDATE by Nico Lambert --------------------------------------------------------
    */
    // Added 2 more categories: Classes and nothing
    switch (category) {
      case "list_animal":
        new_tag.addClass("animal"); 
        iconToDisplay = "pets";
        break;
      case "list_obj":
        new_tag.addClass("object"); 
        iconToDisplay = "package_2"; // Update by Steven Nowak changed symboles displayed to better Match New Style
        break;
      case "list_plant":
        new_tag.addClass("plant"); 
        iconToDisplay = "psychiatry"; 
        break;
      case "list_verb":
        new_tag.addClass("relation"); 
        iconToDisplay = "keyboard_double_arrow_right"; 
        break;
      case "list_person":
        new_tag.addClass("person"); 
        iconToDisplay = "accessibility_new";
        break;
      case "list_class":
        new_tag.addClass("category");
        iconToDisplay = "category"; // Update by Steven Nowak changed symboles displayed to better Match New Style
        break;
      default:
        new_tag.addClass("nothing");
        iconToDisplay = "question_mark"; // Update by Steven Nowak changed symboles displayed to better Match New Style
        break;

      /*
      ------------------------------------------------------------------------------- (END) UPDATE by Nico Lambert --------------------------------------------------------
      */
    }

    new_tag.attr("data-category", category);

    /*
    ----------------------------------------------------------------------------- (START) UPDATE by Nico Lambert --------------------------------------------------------
    */
    // Changed item[item.found_in_column] into item["name_en"]
    // Reason: Seperation between names is no longer needed since we no longer use the CSV Files for Recommandations, instead we use the Database 
    //         -> makes seperation uncessary
    new_tag.html(
      `${
        item["name_en"]
      } 
      | <span class='material-symbols-outlined'>${iconToDisplay}</span>`
    );
    
    return new_tag;
    /*
    ------------------------------------------------------------------------------- (END) UPDATE by Nico Lambert --------------------------------------------------------
    */
  }

  /**
   * Converts a coin ID string into its numeric index.
   * @param {string} coinId - The coin ID to convert.
   * @returns {number} The numeric index corresponding to the coin ID.
   *
   * @Author: Danilo Pantic
   */
  function coinIdToIndex(coinId) {
    return parseInt(coinId.substring(1)) - 1;
  }

  /**
   * Creates an HTML element from a string of HTML.
   * @param {string} htmlString - The HTML string to convert into an element.
   * @returns {Element} The created HTML element.
   *
   * @Author: Danilo Pantic
   */
  function createElementFromHTML(htmlString) {
    const div = document.createElement("div");
    div.innerHTML = htmlString.trim();
    return div.firstChild;
  }

  /**
   * Converts the relation string from the relation editor to a string
   * @returns {string} The relation string as a string
   *
   * @Author: Danilo Pantic
   */
  function htmlToRelationString() {
    let relationString = "";
    $("#relationEditor")
      .children()
      .each(function () {
        const className = $(this).attr("class");
        if (className.includes("id")) {
          relationString += $(this).text();
        } else if (className.includes("op")) {
          const opMap = {
            p_open: "(",
            p_close: ")",
            and: " AND ",
            or: " OR ",
            not: " NOT ",
          };
          const opType = className.split(" ").find((cl) => opMap[cl]);
          relationString += opMap[opType];
        }
      });
    return relationString;
  }

  /**
   * Converts a relation string to HTML and displays it in the relation editor
   * @param {string} relationString The relation string to convert
   * @returns {void}
   *
   * @Author: Mohammed Sayed Mahmod
   */
  function relationStringToHtml(relationString) {
    const opMap = {
      "(": '<span contenteditable="false" class="op p_open">&nbsp;</span>',
      ")": '<span contenteditable="false" class="op p_close">&nbsp;</span>',
      AND: '<span contenteditable="false" class="op and">&nbsp;</span>',
      OR: '<span contenteditable="false" class="op or">&nbsp;</span>',
      NOT: '<span contenteditable="false" class="op not">&nbsp;</span>',
    };
    const idPattern = /C\d+/g;
    let html = relationString
      .replace(/\(/g, opMap["("])
      .replace(/\)/g, opMap[")"])
      .replace(/AND/g, opMap["AND"])
      .replace(/OR/g, opMap["OR"])
      .replace(/NOT/g, opMap["NOT"])
      .replace(
        idPattern,
        (match) => `<span contenteditable="false" class="id">${match}</span>`
      );

    $("#relationEditor").html(html);
  }

  /**
   * Refreshes the relation string in the relation editor
   * @returns {void}
   *
   * @Author: Mohammed Sayed Mahmod
   */
  function refreshRelationString() {
    relationStringToHtml(appState.relationString);

    if (appState._coins.length > 0) {
      const latestCoinId = "C" + appState._coins.length;

      if (appState.relationString.length > 0) {
        appState.relationString += " OR " + latestCoinId;
      } else {
        appState.relationString = latestCoinId;
      }
    } else {
      appState.relationString = "";
    }

    relationStringToHtml(appState.relationString);
  }

  /**
   * Regenerates the SPARQL query based on the current state
   * @returns {void}
   *
   * @Author: Mohammed Sayed Mahmod
   */
  function regenerateQuery() {
    $.ajax({
      method: "POST",
      url: "callback",
      data: {
        action: "generateQuery",
        coins: JSON.stringify(appState.coins),
        relationString: appState.relationString,
        searchType: appState.currentSearchType,
      },
      success: function (response) {
        if (response.success) {
          editor.setValue(spfmt(response.result));
        } else {
          console.error("Failed to generate query: ", response.error);
        }
      },
      error: function (xhr, status, error) {
        console.error("AJAX-Error:", status, error);
      },
    });
  }


 // split of getRecommendations from Mohamed Sayed Mahmod into two functions: getRecommendationsSubObj and getRecommendationsPredicate 

 /**
   * Fetches recommendations for a given query (Only for Subjects and Objects)
   * @param {string} q The query to fetch recommendations for
   * @param {JQuery} target The target element to display the recommendations
   * @param {boolean} is_subject - Boolean to check, wheather recommendation is for subject searchbox or object searchbox, needed for attribute data-type 
   *                               (added per update by Nico Lambert)
   * @param {string} search_type - The type of the current search, either "standard" or "hierarchy-specialise/generalise-simple/absolut / -equivalent" 
   *                               (added per update by Nico Lambert)
   * @param {function} onComplete - A callback function that is executed after the recommendations have been successfully fetched and displayed.
   * @returns {void}
   * @async
   *
   * @Author: Mohammed Sayed Mahmod (because based on former getRecommendations function) , UPDATE by Nico Lambert 
   **/
  function getRecommendationsSubObj(q = "", target, is_subject, search_type, onComplete = () => {}) {
    
    rec = target.parent().children(".rec");
    
    /*
    ----------------------------------------------------------------------------- (START) UPDATE by Nico Lambert --------------------------------------------------------
    */
    // New Variables needed for hierarchy search , to get the uri of the tag element for which the user wants to get generalise / specialice recommendations
    // We always need subj pred and obj uri, because of to be able that the recommendations for generalise / specialice / equivalent also based on the other triple elements 
    // as well as then the user uses the standard search

    side = target.data('side');
    let subj_uri = ""
    let pred_uri = ""
    let obj_uri = ""
    
    // Extracts URI of Subject Predicate and Object from the current coin dictionary for the right coin side
    if (side === 'obverse') {
      for (let i = 0; i < appState.currentCoin.obverse.coin.length; i++) {
        if (appState.currentCoin.obverse.coin[i].type === 'Subj') {
          subj_uri = appState.currentCoin.obverse.coin[i].item.link; 
        } else if (appState.currentCoin.obverse.coin[i].type === 'Predicate') {
          pred_uri = appState.currentCoin.obverse.coin[i].item.link; 
        } else if (appState.currentCoin.obverse.coin[i].type === 'Obj') {
          obj_uri = appState.currentCoin.obverse.coin[i].item.link; 
        }
      }
    }else{
      for (let i = 0; i < appState.currentCoin.reverse.coin.length; i++) {
        if (appState.currentCoin.reverse.coin[i].type === 'Subj') {
          subj_uri = appState.currentCoin.reverse.coin[i].item.link; 
        } else if (appState.currentCoin.reverse.coin[i].type === 'Predicate') {
          pred_uri = appState.currentCoin.reverse.coin[i].item.link;
        } else if (appState.currentCoin.reverse.coin[i].type === 'Obj') {
          obj_uri = appState.currentCoin.reverse.coin[i].item.link;
        }
      }
    }
    /*
    ----------------------------------------------------------------------------- (-END-) UPDATE by Nico Lambert --------------------------------------------------------
    */
    cleanRecommendations(target);

    // Sends out a Request for the Recommandation of the User Input for Subject / Object
    $.ajax({
      method: "POST",
      url: "callback",
      data: {
        action: "getRecommendationsSubObj",
        q: q,
        search_type: search_type, // added per update by Nico Lambert
        subj_uri: subj_uri, // added per update by Nico Lambert
        pred_uri: pred_uri, // added per update by Nico Lambert
        obj_uri: obj_uri, // added per update by Nico Lambert
        is_subject: is_subject, // added per update by Nico Lambert
        side: side, // added per update by Nico Lambert
      },
      success: function (r) {
        appState.latestResponse = r.result;
        
        if (r.success) {
          $.each(r.result, (category, items) => {
            items.forEach((item, index) => {
              
              let rcm = $(
                "<li id='subject"+is_subject+""+side+"'><span class='name'></span><span class='type'><span class='material-symbols-outlined'></span></span></li>"
              );

              /*
              ----------------------------------------------------------------------------- (START) UPDATE by Nico Lambert --------------------------------------------------------
              */
              // Added new Categorys: Classes and nothing
              switch (category) {
                case "list_animal":
                  iconToDisplay = "pets";
                  break;
                case "list_obj":
                  iconToDisplay = "package_2"; // Update Steven Nowak changed displayed symbols to better fit new Style
                  break;
                case "list_plant":
                  iconToDisplay = "psychiatry";
                  break;
                case "list_person":
                  iconToDisplay = "accessibility_new";
                  break;
                case "list_class":
                  iconToDisplay = "category"; // Update Steven Nowak changed displayed symbols to better fit new Style
                  break;
                default:
                  iconToDisplay = "question_mark"; // Update Steven Nowak changed displayed symbols to better fit new Style
                  break;
               /*
               ------------------------------------------------------------------------------- (END) UPDATE by Nico Lambert --------------------------------------------------------
               */
              }
              rcm.attr("data-target", target.attr("data-side"));
              rcm.attr("data-category", category);
              rcm.attr("data-item-id", index);

              /*
              ----------------------------------------------------------------------------- (START) NEW by Nico Lambert --------------------------------------------------------
              */
              // Defines data-type depending on is_subject
              if (is_subject){
                rcm.attr("data-type", "Subj");
              }else{
                rcm.attr("data-type", "Obj")
              }
             
              // Changed item[item.found_in_column] into item["name_en"]
              // Reason: Seperation between names is no longer needed since we no longer use the CSV Files for Recommandations, instead we
              //         use the Database making Seperation uncessary
              rcm.children(".name").text(item["name_en"]);
              rcm.children(".type").children("span").text(iconToDisplay);
              rcm
                .children(".type")
                .html(
                  `${rcm.children(".type").html()} ${category.split("_")[1]}`
                );
              /*
              ------------------------------------------------------------------------------- (END) UPDATE by Nico Lambert --------------------------------------------------------
              */
              rec.children("ul").append(rcm).show();
              
            });
          });
        }

        onComplete();
      },
    });
  }

  /**
   * Fetches recommendations for a given query New: (Only for Predicates)
   * @param {string} q The query to fetch recommendations for
   * @param {JQuery} target The target element to display the recommendations
   * @param {string} search_type - The type of the current search, either "standard" or "hierarchy-specialise/generalise-simple/absolut / -equivalent" 
   *                               (added per update by Nico Lambert)
   * @param {function} onComplete - A callback function that is executed after the recommendations have been successfully fetched and displayed.
   * @returns {void}
   * @async
   *
   * @Author: Mohammed Sayed Mahmod (because based on former getRecommendations function), UPDATE by Nico Lambert
   */
  function getRecommendationsPredicate(q = "", target, search_type, side, onComplete = () => {}) {
    const rec = target.parent().children(".rec");
    /*
    ----------------------------------------------------------------------------- (START) UPDATE by Nico Lambert --------------------------------------------------------
    */
    // New Variables needed for hierarchy search , to get the uri of the tag element for which the user wants to get generalise / specialice / equivalent recommendations
    // We always need subj pred and obj uri, because of to be able that the recommendations for generalise / specialice / equivalent also based on the other triple elements 
    // as well as then the user uses the standard search
    let subj_uri = ""
    let obj_uri = ""
    
    // Extracts URI of Subject Predicate and Object from the current coin dictionary for the right side coin side
    if (side === 'obverse') {
      for (let i = 0; i < appState.currentCoin.obverse.coin.length; i++) {
        if (appState.currentCoin.obverse.coin[i].type === 'Subj') {
          subj_uri = appState.currentCoin.obverse.coin[i].item.link; 
        } else if (appState.currentCoin.obverse.coin[i].type === 'Obj') {
          obj_uri = appState.currentCoin.obverse.coin[i].item.link; 
        }
      }
    }else{
      for (let i = 0; i < appState.currentCoin.reverse.coin.length; i++) {
        if (appState.currentCoin.reverse.coin[i].type === 'Subj') {
          subj_uri = appState.currentCoin.reverse.coin[i].item.link; 
        } else if (appState.currentCoin.reverse.coin[i].type === 'Obj') {
          obj_uri = appState.currentCoin.reverse.coin[i].item.link;
        }
      }
    }
    /*
    ----------------------------------------------------------------------------- (-END-) UPDATE by Nico Lambert --------------------------------------------------------
    */


    cleanRecommendations(target);
    $.ajax({
      method: "POST",
      url: "callback",
      data: {
        action: "getRecommendationsPredicate",
        q: q,
        subj_uri: subj_uri, // Update by Nico Lambert
        obj_uri: obj_uri, // Update by Nico Lambert
        search_type: search_type, // for predicates currently irrelevant, because it can only be "standard" , but added for completness and maybe in the future predicates get
                                  // get a hierarchy as well and then it is needed (Update by  Nico Lambert)
        side: side, // Update by Nico Lambert
      },
      success: function (r) {
        appState.latestResponse = r.result;

        if (r.success) {
          $.each(r.result, (category, items) => {
            items.forEach((item, index) => {
              let rcm = $(
                "<li id='predicate"+side+"'><span class='name'></span><span class='type'><span class='material-symbols-outlined'></span></span></li>"
              );

              /*
              ----------------------------------------------------------------------------- (START) UPDATE by Nico Lambert --------------------------------------------------------
              */
              // Defining which Icon to Display no longer happens
              // Reason: Since Function only Generates Recommandations for Predicates a Separation is no longer Required
              iconToDisplay = "keyboard_double_arrow_right";
              /*
              ------------------------------------------------------------------------------- (END) UPDATE by Nico Lambert --------------------------------------------------------
              */


              rcm.attr("data-target", target.parent().children(".textbox").attr("data-side"));
              rcm.attr("data-category", category);
              rcm.attr("data-item-id", index);

              /*
              ----------------------------------------------------------------------------- (START) UPDATE by Nico Lambert --------------------------------------------------------
              */
              // Chosing which Data-type to Use no longer happens
              // Reason: Since Function only Generates Recommandations for Predicates a Separation is no longer Required
              rcm.attr("data-type", "Predicate");
 
              // Changed item[item.found_in_column] into item["name_en"]
              // Reason: Seperation between names is no longer needed since we no longer use the CSV Files for Recommandations, instead we
              //         use the Database making Seperation uncessary
              rcm.children(".name").text(item["name_en"]);
              rcm.children(".type").children("span").text(iconToDisplay);
              rcm
                .children(".type")
                .html(
                  `${rcm.children(".type").html()} ${category.split("_")[1]}`
                );

              rec.children("ul").append(rcm).show();
              /*
              ------------------------------------------------------------------------------- (END) UPDATE by Nico Lambert --------------------------------------------------------
              */
            });
          });
        }

        onComplete();
      },
    });
  }

  /**
   * Updates the display of the tag container relative to its input element.
   * @param {jQuery} target - The jQuery object representing the target input element.
   *
   * @Author: Danilo Pantic
   */
  function updateTagContainer(target) {
    const tc = target.parent().children(".tagContainer");
    const rec = target.parent().children(".rec");

    target.attr("placeholder", "").val("");
    target.css("padding-left", 42 + tc.width() + "px").focus();

    rec.css("left", 42 + tc.width() + "px");
  }

  /**
   * Adds a tag representing an item to the UI. New: (Now includes Type in Coin)
   * @param {string} category - The category of the item.
   * @param {number} item_id - The ID of the item within its category. (added per update by Nico Lambert)
   * @param {string} side - The side (obverse or reverse) of the coin being edited.
   * @param {jQuery} target - The jQuery object representing the target input element.
   * @param {string} lastSearchType - The type of the last used search, either "standard" or "hierarchy-specialise/generalise-simple/absolut /-equivalent" 
   *                                  (added per update by Nico Lambert)
   *
   * @Author: Danilo Pantic , UPDATE by Nico Lambert 
   */
  function addTag(category, item_id, side, target, type, lastSearchType) {
    const tc = target.parent().children(".tagContainer");
    let item = appState.latestResponse[category][item_id];
    
    
    /*
    ----------------------------------------------------------------------------- (START) NEW by Nico Lambert --------------------------------------------------------
    */
    // if user uses the hierarchy search and selects a tag element, the old element for the current selected field has to get deleteted out of the dict where the selected 
    // elements are saved
    if (lastSearchType != "standard*"){
      for (let i = 0 ; i < appState.currentCoin[side].coin.length; i++) {
        if (appState.currentCoin[side].coin[i].type === type) {
          appState.currentCoin[side].coin.splice(i, 1); 
        }
      }
    }

    // Current coin now includes Type of URI inside Coin Items 
    appState.currentCoin[side].coin.push({
      category: category,
      item: item,
      type: type 

    });

    // after adding new tag, we have to check which hierarchy buttons have to be blocked / active in order to where we get recommendations    
    disableHierarchyButtons(side)

    
    /*
    ------------------------------------------------------------------------------- (END) NEW by Nico Lambert ---------------------------------------------------------
    */


    const new_tag = item2Tag(item, category, tc.children().length);
    
    cleanRecommendations(target);

    /*
    ----------------------------------------------------------------------------- (START) NEW by Nico Lambert --------------------------------------------------------
    */
    // if the user uses the hierarchy search and selects a tag element, the old tag for the current selected field has to get deleteted and the new one has to be added
    if (lastSearchType != "standard*"){
      
      tc.Value="";
      if (type=="Subj"){
        type = "subject"
      }else if (type=="Obj"){
        type = "object"
      }else{
        type = "predicate"
      }
      
      target.parent().parent().children("#standardSearch-"+side+"-"+type).children(".tagContainer").children().remove()
      target.parent().parent().children("#standardSearch-"+side+"-"+type).children(".tagContainer").append(new_tag);
      
    }else{
    /*
    ----------------------------------------------------------------------------- (-END-) NEW by Nico Lambert --------------------------------------------------------
    */
      
      tc.append(new_tag);
      
    }
    updateTagContainer(target);
    
    

    /*
    ----------------------------------------------------------------------------- (START) NEW by Nico Lambert --------------------------------------------------------
    */
    // Disables the abilety to write inside a input field after a tag is added
    if(target.attr('data-searchtype') === 'standard'){
      target.prop('readonly', true);
    }
    /*
    ----------------------------------------------------------------------------- (-END-) NEW by Nico Lambert --------------------------------------------------------
    */

    /*
    ----------------------------------------------------------------------------- (START) NEW by Steven Nowak --------------------------------------------------------
    */
    // Disables the button that displays all subjects / predicates / objects when a tag is added to there respective input field
    // Reason: Without this the buttons could be used to add a second subject / predicate / object to a search field which the Code does not support creating errors
    var role = target.parent().find('input[data-role]').attr('data-role');
    if (side === "obverse") {
      if (role === "coin-description-subject") {
        document.querySelector('[data-side="obverse"][data-action="listAllSubj"]').disabled = true;
      } else if (role === "coin-description-object") {
        document.querySelector('[data-side="obverse"][data-action="listAllObj"]').disabled = true;
      } else {
        document.querySelector('[data-side="obverse"][data-action="listAllPredicates"]').disabled = true;
      }
    } else  {
      if (role === "coin-description-subject") {
        document.querySelector('[data-side="reverse"][data-action="listAllSubj"]').disabled = true;
      } else if (role === "coin-description-object") {
        document.querySelector('[data-side="reverse"][data-action="listAllObj"]').disabled = true;
      } else {
        document.querySelector('[data-side="reverse"][data-action="listAllPredicates"]').disabled = true;
      }
    }
    /*
    ------------------------------------------------------------------------------- (END) NEW by Steven Nowak --------------------------------------------------------
    */
    
  }

  /**
   * Adds a tag representing an item to the UI.
   * @param {string} category - The category of the item.
   * @param {Object} item - The item to add.
   * @param {string} type - The type of the item. (added per update by Steven Nowak)
   * @param {string} side - The side (obverse or reverse) of the coin being edited.
   * @param {jQuery} target - The jQuery object representing the target input element.
   * @returns {void}
   *
   * @Author: Mohammed Sayed Mahmod, UPDATE by Steven Nowak, UPDATE by Nico Lambert
   */
  function addTagByItem(category, item, type, side, target) {
    const tc = target.parent().children(".tagContainer");

    /*
    ----------------------------------------------------------------------------- (START) UPDATE by Steven Nowak --------------------------------------------------------
    */
    // Current coin updated to now includes type (absolute superclass) of URI inside coin items
    appState.currentCoin[side].coin.push({
      category: category,
      item: item,
      type: type 
    });
    /*
    ------------------------------------------------------------------------------- (END) UPDATE by Steven Nowak --------------------------------------------------------
    */
    

    const new_tag = item2Tag(item, category);
    cleanRecommendations(target);
    tc.append(new_tag);
  

    

    /*
    ----------------------------------------------------------------------------- (START) NEW by Nico Lambert --------------------------------------------------------
    */
    // Disables Writing insde input field after adding a tag
    // Reason: Without this the user could add a second subject / predicate / object to a search field which the Code does not support creating errors
    target.prop('readonly',true);  
    /*
    ------------------------------------------------------------------------------- (END) NEW by Nico Lambert --------------------------------------------------------
    */



    /*
    ----------------------------------------------------------------------------- (START) NEW by Steven Nowak --------------------------------------------------------
    */
    // Disables the button that displays all subjects / predicates / objects when a tag is added to there respective input field
    // Reason: Without this the buttons could be used to add a second subject / predicate / object to a search field which the Code does not support creating errors
    if (side === "obverse") {
      if (type === "Subj") {
        document.querySelector('[data-side="obverse"][data-action="listAllSubj"]').disabled = true;
      } else if (type === "Obj") {
        document.querySelector('[data-side="obverse"][data-action="listAllObj"]').disabled = true;
      } else {
        document.querySelector('[data-side="obverse"][data-action="listAllPredicates"]').disabled = true;
      }
    } else  {
      if (type === "Subj") {
        document.querySelector('[data-side="reverse"][data-action="listAllSubj"]').disabled = true;
      } else if (type === "Obj") {
        document.querySelector('[data-side="reverse"][data-action="listAllObj"]').disabled = true;
      } else {
        document.querySelector('[data-side="reverse"][data-action="listAllPredicates"]').disabled = true;
      }
    }

    /*
    ------------------------------------------------------------------------------- (END) NEW by Steven Nowak --------------------------------------------------------
    */

  }

  /**
   * Removes a tag from the UI.
   * @param {jQuery} target - The jQuery object representing the target input element.
   *
   * @Author: Mohammed Sayed Mahmod, UPDATE by Nico Lambert, UPDATE by Steven Nowak
   */
  function removeTag(target) {
    const tc = target.parent().children(".tagContainer");

    const side = $(target).attr("data-side");
    const type = $(target).attr("data-role");

    /*
    ----------------------------------------------------------------------------- (START) UPDATE by Steven Nowak --------------------------------------------------------
    */
    // Current Coin gets updated based on the search field gets deleted
    // Reason: Since input fields are seperated into subject, predicate and object deleting the tags no longer works by a fixed order of object tag, predicate tag and finaly subject tag.
    // Which is why the code was updated to always delete the by the user chosen tag 
    $.each(appState.currentCoin[side].coin, function(index, element) {
      switch (type) {
        case "coin-description-subject":
          if (element.type == "Subj") {
            appState.currentCoin[side].coin.splice(index, 1);
          }
          break;
        case "coin-description-predicate":
          if (element.type == "Predicate") {
            appState.currentCoin[side].coin.splice(index, 1);
          }
          break;
        case "coin-description-object":
          if (element.type == "Obj") {
            appState.currentCoin[side].coin.splice(index, 1);
          }
          break;
      }
    });
    /*
    ------------------------------------------------------------------------------- (END) UPDATE by Steven Nowak --------------------------------------------------------
    */


    /*
    ------------------------------------------------------------------------------- (START) NEW by Nico Lambert -------------------------------------------------------
    */
    //After removing a tag, checks which hierarchy buttons have to be blocked / active based on new set of recommendations for possible coins    
    disableHierarchyButtons(side)
    /*
    ------------------------------------------------------------------------------- (END) NEW by Nico Lambert ---------------------------------------------------------
    */

    cleanRecommendations(target);
    tc.children().last().remove();
    updateTagContainer(target);

    /*
    ----------------------------------------------------------------------------- (START) NEW by Nico Lambert --------------------------------------------------------
    */
    // Reenables the Abilety to write inside input field after the tag is removed from it
    target.prop('readonly', false);
    /*
    ------------------------------------------------------------------------------- (END) NEW by Nico Lambert --------------------------------------------------------
    */

    
    /*
    ----------------------------------------------------------------------------- (START) NEW by Steven Nowak --------------------------------------------------------
    */
    // Reenables the button that displays all Subbjects /Predicates /Objects when the tag is removed from the respective input field
    if (side === "obverse") {
      if (type === "coin-description-subject") {
        document.querySelector('[data-side="obverse"][data-action="listAllSubj"]').disabled = false;
      } else if (type === "coin-description-object") {
        document.querySelector('[data-side="obverse"][data-action="listAllObj"]').disabled = false;
      } else {
        document.querySelector('[data-side="obverse"][data-action="listAllPredicates"]').disabled = false;
      }
    } else  {
      if (type === "coin-description-subject") {
        document.querySelector('[data-side="reverse"][data-action="listAllSubj"]').disabled = false;
      } else if (type === "coin-description-object") {
        document.querySelector('[data-side="reverse"][data-action="listAllObj"]').disabled = false;
      } else {
        document.querySelector('[data-side="reverse"][data-action="listAllPredicates"]').disabled = false;
      }
    }
    /*
    ------------------------------------------------------------------------------- (END) NEW by Steven Nowak --------------------------------------------------------
    */
  }

  /**
   * Clears all recommendations from the display.
   * @param {jQuery} target - The jQuery object representing the target element.
   *
   * @Author: Danilo Pantic
   */
  function cleanRecommendations(target) {
    const rec = target.parent().parent().parent().find(".rec");
    rec.each(function () {
      $(this).children("ul").empty();
    })
  }

  /**
   * Clears all fields and resets the form to its initial state.
   *
   * @Author: Danilo Pantic, UPDATE by Nico Lambert and Steven Nowak
   */
  function clearForm() {
    appState.currentCoin = {
      obverse: { coin: [], keywords: [] },
      reverse: { coin: [], keywords: [] },
    };

    let kec = $(".keywordContainer");

    $("#searchBox input[type=text]").val("");
    kec.empty();

    $("#searchBox .tagContainer").each(function () {
      $(this).empty();

      updateTagContainer(
        $(this).parent().children("[data-role^='coin-description-']")
      );
    });


    /*
    ----------------------------------------------------------------------------- (START) NEW by Nico Lambert --------------------------------------------------------
    */
    // Reenables the Abilety to write in the input fields after the tags are removed and restores the placeholder Ttxt
    $("#searchBox .search  input[type=text][data-role='coin-description-subject']").attr("placeholder","Subject:")        
                                                                                   .prop('readonly',false);
    $("#searchBox .search  input[type=text][data-role='coin-description-predicate']").attr("placeholder","Predicate:")    
                                                                                     .prop('readonly',false);
    $("#searchBox .search  input[type=text][data-role='coin-description-object']").attr("placeholder","Object:")
                                                                                  .prop('readonly',false);

    // Take the focus off the field. This means that after clicking "Add Coin to query" or "Clean Input" or "Edit Coin" 
    // the user does not start directly in the field and therefore cannot enter anything there directly.
    $("#searchBox .search  input[type=text][data-role='coin-description-subject']").blur();
    $("#searchBox .search  input[type=text][data-role='coin-description-predicate']").blur();
    $("#searchBox .search  input[type=text][data-role='coin-description-object']").blur();
  
    /*
    ------------------------------------------------------------------------------- (END) NEW by Nico Lambert --------------------------------------------------------
    */

    

    /*
    ----------------------------------------------------------------------------- (START) NEW by Steven Nowak & Nico Lambert --------------------------------------------------------
    */

    // Hierarchy buttons are disabled if there is no tag -> when coin is added to query - no tag for current coin
    let listAllButtons = document.querySelectorAll('[data-action^="simple"]');
    listAllButtons.forEach(button => {
      button.disabled = true;
    });
    listAllButtons = document.querySelectorAll('[data-action^="absolute"]');
    listAllButtons.forEach(button => {
      button.disabled = true;
    });
    listAllButtons = document.querySelectorAll('[data-action^="similar"]');
    listAllButtons.forEach(button => {
      button.disabled = true;
    });

    //Reenables the buttons that displays all subjects / predicates / objects when the input fields are cleared
    //by looping through all list-all buttons for each side and setting disable to false
    listAllButtons = document.querySelectorAll('[data-action^="listAll"]');
    listAllButtons.forEach(button => {
      button.disabled = false;
    });
    /*
    ------------------------------------------------------------------------------- (END) NEW by Steven Nowak & Nico Lambert --------------------------------------------------------
    */
  }

  /**
   * Renders the coins data into the UI based on the current application state.
   *
   * @Author: Mohammed Sayed Mahmod , UPDATE by Nico Lambert 
   */
  function renderCoins() {
    var coinTableBody = $("#coincatalogue .coin-tbody");
    coinTableBody.empty();

    appState.coins.forEach(function (coin, index) {
      var coinId = "C" + (index + 1);

      var coinRow = $("<div>").addClass("coin-tr").attr("data-id", coinId);
      var mainContent = $("<div>").addClass("coin-tr-main");
      mainContent.append($("<span>").text(coinId));

      function createSideContent(side) {
        var sideContent = $("<span>");

        /*
        ----------------------------------------------------------------------------- (START) UPDATE by Nico Lambert --------------------------------------------------------
        */
        // The problem was that we changed the way the triple parts were entered. Previously, the input was in one field, so you could use the order and the category 
        // to determine which part of the triple the content from the dict was. However, we changed it so that you enter the subject, predicate and object separately 
        // (1 per field). The order in which the subject, predicate and object are saved in the dict is not clear, because that depends on the order in which the user 
        // entered them. As a result, the tags for "Queried Items" were in the wrong order. This is why we added the "type" property. Now the tag elemnt is first set 
        // for the subj (if there is one), then for the predicate (if there is one), and finally for the object (if there is one). The only problem now is that the 
        // entries from the dict have to be processed three times.
        var tagContainer = $("<div>").addClass("tagContainer");
        side.coin.forEach(function (coinItem) {
          if (coinItem.type == "Subj"){

            var tag = item2Tag(
              coinItem.item,
              coinItem.category,
              tagContainer.children().length
            );

            tagContainer.append(tag);
          }
        });

        side.coin.forEach(function (coinItem) {
          if (coinItem.type == "Predicate"){

            var tag = item2Tag(
              coinItem.item,
              coinItem.category,
              tagContainer.children().length
            );

            tagContainer.append(tag);
           
          }
        });

        side.coin.forEach(function (coinItem) {
          if (coinItem.type == "Obj"){

            var tag = item2Tag(
              coinItem.item,
              coinItem.category,
              tagContainer.children().length
            );

            tagContainer.append(tag);
          }
        });
        /*
        ------------------------------------------------------------------------------- (END) UPDATE by Nico Lambert --------------------------------------------------------
        */

        sideContent.append(tagContainer);

        var keywordsDiv = $("<div>").addClass("keywords");
        var title = $("<div>")
          .addClass("title")
          .append($("<span>").text("Keywords:"));
        var keywordList = $("<div>").addClass("keywordlist");

        /*
        ----------------------------------------------------------------------------- (START) UPDATE by Steven Nowak ------------------------------------------
        */
        //change, that the keywords div is only displayed, if there is more than one keyword
        (side.keywords).forEach(function (kw) {
          var keywordSpan = $("<span>")
            .addClass("keyword")
            .text(kw.text)
            .attr("data-negated", kw.negated ? "true" : "false");

          keywordList.append(keywordSpan);
          keywordsDiv.append(title).append(keywordList);
        });
        /*
        ------------------------------------------------------------------------------- (END) UPDATE by Steven Nowak ------------------------------------------
        */
        sideContent.append(keywordsDiv);
        return sideContent;
      }

      mainContent.append(createSideContent(coin.obverse));
      mainContent.append(createSideContent(coin.reverse));
      mainContent.append(
        $(`<span>
            <div class="editRow">
              <span class="material-symbols-outlined" data-action="editCoin" data-id="${coinId}">
                edit
              </span>
              <span class="material-symbols-outlined" data-action="deleteCoin" data-id="${coinId}">
                delete
              </span>
            </div>
          </span>`)
      );

      coinRow.append(mainContent);
      coinTableBody.append(coinRow);
    });

    $("#searchActions .searchcoin").prop(
      "disabled",
      appState._coins.length === 0
    );
  }

  /**
   * Inserts a given HTML node at the end of the relation editor.
   * @param {Node} node - The HTML node to be appended.
   *
   * @Author: Danilo Pantic
   */
  function insertAtEnd(node) {
    const relationEditor = $("#relationEditor");

    relationEditor.append(node);

    appState.relationString = htmlToRelationString();
    regenerateQuery();
  }

  /**
   * Calculates the width of the arrow in a tooltip based on the number of tooltips present.
   * @returns {number} The calculated width of the arrow.
   *
   * @Author: Mohammed Sayed Mahmod
   */
  function calcArrowWidth() {
    const num_tooltips = $(".tooltip-container .tooltip").length;

    if (num_tooltips > 1) {
      return (
        $(".tooltip-container").outerWidth() -
        $(".tooltip-container .tooltip").first().outerWidth() / 2 -
        $(".tooltip-container .tooltip").last().outerWidth() / 2 -
        5
      );
    }
    return 5;
  }

  
  /**
   * Performs a search based on the current query in the SPARQL editor.
   * @returns {void}
   *
   * @Author: Danilo Pantic
   */
  function performSearch() {
    $("#loadingSymbol").removeClass("hidden");
    $("#moveableStage").attr("data-state", "results");
    $.ajax({
      method: "POST",
      url: "callback",
      data: {
        action: "searchCoin",
        q: editor.getValue(),
        searchType: appState.currentSearchType,
      },
      success: function (r) {
        $("#loadingSymbol").addClass("hidden");
        $("#numSearchResults").html(r.result.length);

        if (r.success) {
          appState.latestCoinResult = r.result;
          appState.sortedCoinResult = [...r.result];
          appState.totalPages = Math.ceil(
            appState.sortedCoinResult.length / appState.resultsPerPage
          );
          appState.currentPage = 1;
          appState.renderCurrentPage();
        }
      },
    });
  }

  /**
   * Adds the currently described coin to the query state.
   * @returns {void}
   *
   * @Author: Danilo Pantic
   */
  function addCoinToQuery() {
    let obverseKeywords = $("#front .keywordContainer span.keyword")
      .map(function () {
        return {
          text: $(this).find(".label").text(),
          negated: $(this).attr("data-negated") === "true",
        };
      })
      .get();

    let reverseKeywords = $("#back .keywordContainer span.keyword")
      .map(function () {
        return {
          text: $(this).find(".label").text(),
          negated: $(this).attr("data-negated") === "true",
        };
      })
      .get();

    appState.currentCoin.obverse.keywords = obverseKeywords;
    appState.currentCoin.reverse.keywords = reverseKeywords;

    appState.addCoin(appState.currentCoin);

    clearForm();
  }
  

  /**
   * Groups the results by a specified property.
   * @param {Array} results - The results to group.
   * @param {string} groupBy - The property to group by.
   * @returns {Object} The grouped results.
   *
   * @Author: Mohammed Sayed Mahmod
   */
  function groupResults(results, groupBy) {
    return results.reduce((acc, result) => {
      const key = result[groupBy] || "uncategorized";
      if (!acc[key]) {
        acc[key] = [];
      }
      acc[key].push(result);
      return acc;
    }, {});
  }

  /**
   * Sorts the results based on the current sort settings.
   * @returns {void}
   * @async
   *
   * @Author: Mohammed Sayed Mahmod
   */
  function sortResults() {
    const sortBy = $("#sortSelect").val();
    const sortDirection = $("#sortDirection").val();

    appState.sortedCoinResult.sort((a, b) => {
      let valueA = a[sortBy];
      let valueB = b[sortBy];

      if (typeof valueA === "number" && typeof valueB === "number") {
        return sortDirection === "ascending"
          ? valueA - valueB
          : valueB - valueA;
      } else {
        valueA = String(valueA || "").toLowerCase();
        valueB = String(valueB || "").toLowerCase();

        if (valueA < valueB) return sortDirection === "ascending" ? -1 : 1;
        if (valueA > valueB) return sortDirection === "ascending" ? 1 : -1;
        return 0;
      }
    });
  }

  /**
   * Renders the grouped results into the UI.
   * @param {Object} groupedResults - The grouped results to render.
   * @returns {void}
   * @async
   *
   * @Author: Mohammed Sayed Mahmod
   */
  function renderResults(groupedResults) {
    const resultContainer = $("#resultContainer");
    resultContainer.empty();

    $.each(groupedResults, (category, coins) => {
      let categoryDiv = $("<div>")
        .addClass("category")
        .append($("<span>").text(category));
      let categoryContainer = $("<div>").addClass("category-container");

      coins.forEach((coin) => {
        let weight = coin.weight != null ? `${coin.weight.toFixed(2)}g` : null;

        let extraInfoItems = [
          coin.date,
          coin.maxDiameter ? `${coin.maxDiameter}mm` : null,
          weight,
        ].filter((item) => item != null);
        let extraInfoText = extraInfoItems.join(", ");

        let resultItem = $("<div>")
          .addClass("result-item")
          .addClass(coin.type)
          .attr("data-redirect", coin.url)
          .append(
            $("<div>")
              .addClass("result-item-top")
              .append(
                $("<div>")
                  .addClass("result-item-top-id")
                  .append($("<span>").text(coin.id))
              )
              .append(
                $("<img>")
                  .attr("src", coin.thumbnailObverse)
                  .addClass("obverse")
              )
              .append(
                $("<img>")
                  .attr("src", coin.thumbnailReverse)
                  .addClass("reverse")
              )
          )
          .append(
            $("<div>")
              .addClass("result-item-bottom")
              .append(
                $("<p>")
                  .addClass("result-item-bottom-location")
                  .append($("<span>").addClass("location").html(coin.location))
                  .append(
                    $("<span>")
                      .addClass("region")
                      .text(coin.region || "")
                  )
              )
              .append(
                $("<p>")
                  .addClass("result-item-bottom-extra")
                  .text(extraInfoText)
              )
              .append(
                $("<div>")
                  .addClass("result-item-bottom-description")
                  .append(
                    $("<p>").html(
                      `<span>Obverse:</span> ${coin.descriptionObverse}`
                    )
                  )
                  .append(
                    $("<p>").html(
                      `<span>Reverse:</span> ${coin.descriptionReverse}`
                    )
                  )
              )
          );
        categoryContainer.append(resultItem);
      });

      resultContainer.append(categoryDiv.append(categoryContainer));
    });
  }

  /**
   * Updates the pagination controls based on the current state.
   * @returns {void}
   * @async
   *
   * @Author: Danilo Pantic
   */
  function updatePaginationControls() {
    $("#pageInfo").text(
      `Page ${appState.currentPage} of ${appState.totalPages}`
    );
    $("#prevPage").prop("disabled", appState.currentPage === 1);
    $("#nextPage").prop(
      "disabled",
      appState.currentPage === appState.totalPages
    );
  }

  //------------------------------------ (START) UPDATE by Nico Lambert --------------------------------------------------------
  // Replaced tutuorial with userManual
  $("a[href='#userManual']").click(function (e) {
    e.preventDefault();

    // path to our user manual pdf
    var pdfPath = '../static/Benutzerhandbuch.pdf';
    // oprns user manual in new window
    window.open(pdfPath, '_blank');
    
  });
  //------------------------------------ (END) UPDATE by Nico Lambert --------------------------------------------------------
  function cleanHierachy() {
    $('[data-searchtype="hierarchy"]').each(function() {
      const target = $(this);
      const role = target.data('role'); 
      target.val("");
      if(role === 'coin-description-subject'){
        target.attr("placeholder","Subject:");
      } else if (role === 'coin-description-object'){
        target.attr("placeholder","Object:");
      } 
    });    
    const hierarchyInputs = document.querySelectorAll('[id*="hierarchySearch-"]');
    const standartInputs = document.querySelectorAll('[id*="standardSearch-"]');

    hierarchyInputs.forEach(input => {
      input.style.display = "none";
    });
    standartInputs.forEach(input => {
      input.style.display = "flex";
    });
  }

  

  $("[data-tooltip]").hover(
    function () {
      var tooltipText = $(this).attr("data-tooltip");
      var offset = $(this).offset();

      var $tooltip = $('<div class="tooltip-info"></div>')
        .text(tooltipText)
        .appendTo("body");
      var tooltipWidth = $tooltip.outerWidth();

      var tooltipPositionLeft =
        offset.left + $(this).width() / 2 - tooltipWidth / 2;
      var tooltipPositionTop = offset.top + $(this).height() + 10;

      if (tooltipPositionLeft < 0) {
        tooltipPositionLeft = 0;
      } else if (tooltipPositionLeft + tooltipWidth > $(window).width()) {
        tooltipPositionLeft = $(window).width() - tooltipWidth;
      }

      $tooltip.css({ left: tooltipPositionLeft, top: tooltipPositionTop });
    },
    function () {
      $(".tooltip-info").remove();
    }
  );

  //Made by Steven Nowak [data-tooltip].hover copied but with cooldown to only display tooltip after 1s of hovering (for hierachy buttons)
  $("[data-tooltipButton]").hover(
    function () {
      cooldown = setTimeout(() => {
        var tooltipText = $(this).attr("data-tooltipButton");
        var offset = $(this).offset();

        var $tooltip = $('<div class="tooltip-info"></div>')
          .text(tooltipText)
          .appendTo("body");
        var tooltipWidth = $tooltip.outerWidth();

        var tooltipPositionLeft =
          offset.left + $(this).width() / 2 - tooltipWidth / 2;
        var tooltipPositionTop = offset.top + $(this).height() + 10;

        if (tooltipPositionLeft < 0) {
          tooltipPositionLeft = 0;
        } else if (tooltipPositionLeft + tooltipWidth > $(window).width()) {
          tooltipPositionLeft = $(window).width() - tooltipWidth;
        }

        $tooltip.css({ left: tooltipPositionLeft, top: tooltipPositionTop });
      }, 1000);
      $(this).data("cooldown", cooldown);
    },
    function () {
      clearTimeout($(this).data("cooldown"));
      $(".tooltip-info").remove();
    }
  );


  $("body").on("click", "[data-action=deleteCoin]", (e) => {
    var coinId = $(e.currentTarget).attr("data-id");
    var coinIndex = coinIdToIndex(coinId);

    appState.coins.splice(coinIndex, 1);
    renderCoins();
  });

  $("body").on("click", "[data-action=editCoin]", (e) => {
    var coinId = $(e.currentTarget).attr("data-id");
    var coinIndex = coinIdToIndex(coinId);
    var coin = appState.coins[coinIndex];

    /*
    ----------------------------------------------------------------------------- (START) NEW by Nico Lambert & Steven Nowak ---------------------------------------------
    */
    // Deletes coin request from .coins as without it we would make a copy instead of editing it.
    // processed coin must get deleted out of all coins - should not be a copy
    appState.coins.splice(coinIndex, 1); 
    /*
    ------------------------------------------------------------------------------- (END) NEW by Nico Lambert & Steven Nowak ---------------------------------------------
    */
    clearForm();


    /*
    ----------------------------------------------------------------------------- (START) UPDATE by Steven Nowak ---------------------------------------------------------
    */
    // Adjustment so that items are added to the correct input field during editing. Adjustment was necessary because we now have three triple parts fields, 
    // otherwise the entire triple would be in each field for the corresponding coin side
    const obverseKeywordsContainer = $(
      "#searchBox [data-side='obverse'] .keywordContainer"
    );
    const reverseKeywordsContainer = $(
      "#searchBox [data-side='reverse'] .keywordContainer"
    );

    $.each(coin.obverse.coin, (index, coinItem) => {
      switch (coinItem.type){
        case "Subj":
          const obverseQuerySub = $(
            "#searchBox [data-side='obverse'] [data-role^='coin-description-subject'] "
          );
          addTagByItem(coinItem.category, coinItem.item, coinItem.type, "obverse", obverseQuerySub);
          break;
        case "Predicate":
          const obverseQueryPre = $(
            "#searchBox [data-side='obverse'] [data-role='coin-description-predicate']"
          );
          addTagByItem(coinItem.category, coinItem.item, coinItem.type, "obverse", obverseQueryPre);
          break;
        case "Obj":
          const obverseQueryObj = $(
            "#searchBox [data-side='obverse'] [data-role='coin-description-object']"
          );
          addTagByItem(coinItem.category, coinItem.item, coinItem.type, "obverse", obverseQueryObj);
          break;
        default:
          alert("Error Invalid Type for Obverse")
          break;
      }  
      /*
      ------------------------------------------------------------------------------- (END) UPDATE by Steven Nowak ---------------------------------------------------------
      */


      /*
      ----------------------------------------------------------------------------- (START) NEW by Nico Lambert --------------------------------------------------------
      */
      // This is to remove the focus from the field. This means that it ensures that you do not start in the field after the last action and therefore cannot enter 
      // anything there directly.
      $("#searchBox .search  input[type=text][data-role='coin-description-subject']").blur();
      $("#searchBox .search  input[type=text][data-role='coin-description-predicate']").blur();
      $("#searchBox .search  input[type=text][data-role='coin-description-object']").blur();
      /*
      ------------------------------------------------------------------------------- (END) NEW by Nico Lambert --------------------------------------------------------
      */

    });

    $.each(coin.reverse.coin, (index, coinItem) => {
      switch (coinItem.type){
        case "Subj":
          const reverseQuerySub = $(
            "#searchBox [data-side='reverse'] [data-role='coin-description-subject']"
          );
          addTagByItem(coinItem.category, coinItem.item, coinItem.type, "reverse", reverseQuerySub);
          break;
        case "Predicate":
          const reverseQueryPre = $(
            "#searchBox [data-side='reverse'] [data-role='coin-description-predicate']"
          );
          addTagByItem(coinItem.category, coinItem.item, coinItem.type, "reverse", reverseQueryPre);
          break;
        case "Obj":
          const reverseQueryObj = $(
            "#searchBox [data-side='reverse'] [data-role='coin-description-object']"
          );
          addTagByItem(coinItem.category, coinItem.item, coinItem.type, "reverse", reverseQueryObj);
          break;
        default:
          alert("Error Invalid Type for Reverse")
          break;
      } 

      /*
      ----------------------------------------------------------------------------- (START) NEW by Nico Lambert --------------------------------------------------------
      */
      // This is to remove the focus from the field. This means that it ensures that you do not start in the field after the last action and therefore cannot enter 
      // anything there directly.
      $("#searchBox .search  input[type=text][data-role='coin-description-subject']").blur();
      $("#searchBox .search  input[type=text][data-role='coin-description-predicate']").blur();
      $("#searchBox .search  input[type=text][data-role='coin-description-object']").blur();
      
    });

    // After the tags are added into the input fields, we have to check which hierarchy buttons have to be blocked / active based on if they generate at least 1 recommendation    
    disableHierarchyButtons("obverse");
    disableHierarchyButtons("reverse");
    /*
    ------------------------------------------------------------------------------- (END) NEW by Nico Lambert ---------------------------------------------------------
    */

    /*
    ----------------------------------------------------------------------------- (START) UPDATE by Steven Nowak ---------------------------------------------------------
    */
    // Function updated to now work with our new keyword container and changes to negation logik
    function appendKeywords(keywords, container) {
      keywords.forEach((kw) => {
        let keywordSpan = $("<span></span>", {
          class: "keyword",
          "data-negated": kw.negated ? "true" : "false",
        }).appendTo(container);

        $("<span></span>", {
          class: "label",
          text: kw.text,
        }).appendTo(keywordSpan);

        //Gives each keyword a button to edit it
        $('<button></button>', {
          class: "editKeywordButton",
          html: '<i class="fa-solid fa-pencil"></i>', 
          "data-action": "editKeyword",
          "data-label": kw.text
        }).appendTo(keywordSpan);
      });
    }

    appendKeywords(coin.obverse.keywords, obverseKeywordsContainer);
    appendKeywords(coin.reverse.keywords, reverseKeywordsContainer);
    /*
    ------------------------------------------------------------------------------- (END) UPDATE by Steven Nowak ---------------------------------------------------------
    */


    renderCoins();
  });

  $("body").on("click", "[data-target][data-category][data-item-id]", (e) => {
    const current = $(e.currentTarget);
    const target = current
      .parent()
      .parent()
      .parent()
      .children("[data-role^='coin-description-']");
    const side = current.attr("data-target");

    
    cleanRecommendations(target);



    let category = current.attr("data-category");
    let item_id = current.attr("data-item-id");
    /*
    ----------------------------------------------------------------------------- (START) NEW by Nico Lambert --------------------------------------------------------
    */

    // hierarchySearch field isn't allowed to be visible anymore, after user added Tag, standard search field has to be visible with all buttons
    cleanHierachy();
        
        
    // we need to save, whether the current item is subject , predicate or object. This is necessary for the addTag function,
    // it is also required to asigne each tag to the correct input field if the user wants to edit there coin requests 
    let type = current.attr("data-type"); 
    /*
    ------------------------------------------------------------------------------- (END) NEW by Nico Lambert --------------------------------------------------------
    */
    addTag(category, item_id, side, target, type, lastSearchType);
  });

  
  $("[data-role^='coin-description']").keyup((e) => {
    const role = $(e.target).data('role'); 
    const searchtype = $(e.target).data('searchtype'); // NEW by Steven Nowak & Nico Lambert
    const target = $(e.currentTarget);
    const side = target.data('side'); // NEW by Steven Nowak & Nico Lambert
    const isAlphabetChar = /[a-zA-Z]/.test(e.key);
    clearTimeout(cooldown);
    
    /*
    ----------------------------------------------------------------------------- (START) UPDATE by Nico Lambert --------------------------------------------------------
    */
    // edit of length - now trigger if user enters at least one char - bevore it was > 2 
    if (target.val().length > 0 && isAlphabetChar) {

      cleanRecommendations(target);
      /*
        ----------------------------------------------------------------------------- (START) NEW by Steven Nowak --------------------------------------------------------
      */
      // Disables the button that displays all subject/predicates/objects when there respective search field is not empty
      // Reason: The input of the field interfers with the function of the Button  
      if (side === "obverse") {
        if (role === "coin-description-subject") {
          document.querySelector('[data-side="obverse"][data-action="listAllSubj"]').disabled = true;
        } else if (role === "coin-description-object") {
          document.querySelector('[data-side="obverse"][data-action="listAllObj"]').disabled = true;
        } else {
          document.querySelector('[data-side="obverse"][data-action="listAllPredicates"]').disabled = true;
        }
      } else  {
        if (role === "coin-description-subject") {
          document.querySelector('[data-side="reverse"][data-action="listAllSubj"]').disabled = true;
        } else if (role === "coin-description-object") {
          document.querySelector('[data-side="reverse"][data-action="listAllObj"]').disabled = true;
        } else {
          document.querySelector('[data-side="reverse"][data-action="listAllPredicates"]').disabled = true;
        }
      }
      /*
        ------------------------------------------------------------------------------- (END) NEW by Steven Nowak --------------------------------------------------------
      */

      cooldown = setTimeout(() => {
        
        // Adaptation: we now have different recommendations functions, depending on the role a different one is used. called
        if (searchtype === 'standard'){
          cleanHierachy();
          if (role === 'coin-description-predicate') {
            getRecommendationsPredicate(target.val(), target, "standard", side); 
            lastSearchType = "standard";
          } else if (role === 'coin-description-subject'){
            getRecommendationsSubObj(target.val(), target, true, "standard"); 
            lastSearchType = "standard";
          } else if (role === 'coin-description-object'){
            getRecommendationsSubObj(target.val(), target, false, "standard"); 
            lastSearchType = "standard";
          }
        } else if (searchtype === 'hierarchy'){

          if (role === 'coin-description-subject'){
            getRecommendationsSubObj(target.val(), target, true, lastSearchType)
          } else if (role === 'coin-description-object'){
            getRecommendationsSubObj(target.val(), target, false, lastSearchType); 
          }

        }
        
        
      }, 500);
    } else {
    /*
    ------------------------------------------------------------------------------- (END) UPDATE by Nico Lambert --------------------------------------------------------
    */
      cleanRecommendations(target);
      if (e.key === "Backspace" && target.val().length === 0 && searchtype === 'standard') {
        cleanHierachy();
        removeTag(target);


        /*
        ----------------------------------------------------------------------------- (START) NEW by Steven Nowak --------------------------------------------------------
        */
        // Disables the button that displays all subject/predicates/objects when there respective search field is not empty
        // Reason: The input of the field interfers with the function of the Button  
        if (side === "obverse") {
          if (role === "coin-description-subject") {
            document.querySelector('[data-side="obverse"][data-action="listAllSubj"]').disabled = false;
          } else if (role === "coin-description-object") {
            document.querySelector('[data-side="obverse"][data-action="listAllObj"]').disabled = false;
          } else {
            document.querySelector('[data-side="obverse"][data-action="listAllPredicates"]').disabled = false;
          }
        } else  {
          if (role === "coin-description-subject") {
            document.querySelector('[data-side="reverse"][data-action="listAllSubj"]').disabled = false;
          } else if (role === "coin-description-object") {
            document.querySelector('[data-side="reverse"][data-action="listAllObj"]').disabled = false;
          } else {
            document.querySelector('[data-side="reverse"][data-action="listAllPredicates"]').disabled = false;
          }
        }
        /*
        ------------------------------------------------------------------------------- (END) NEW by Steven Nowak --------------------------------------------------------
        */
        

        /*
        ----------------------------------------------------------------------------- (START) NEW by Nico Lambert --------------------------------------------------------
        */
        // This is to have the placeholder in the input field when the input field is empty again.
        // Also, since the hierachy search is based on the tag elements of the input fields,
        // removing a tag also causes all the hierarchy buttons of the respective input field to get disabled 
        if (role === 'coin-description-predicate') {
          target.attr("placeholder","Predicate:");
        } else if (role === 'coin-description-subject'){
          target.attr("placeholder","Subject:");
          document.querySelector('[data-side="'+side+'"][data-action="simpleSpecialiseSubject"]').disabled = true;
          document.querySelector('[data-side="'+side+'"][data-action="absoluteSpecialiseSubject"]').disabled = true;
          document.querySelector('[data-side="'+side+'"][data-action="simpleGeneraliseSubject"]').disabled = true;
          document.querySelector('[data-side="'+side+'"][data-action="absoluteGeneraliseSubject"]').disabled = true;
          document.querySelector('[data-side="'+side+'"][data-action="similarSubject"]').disabled = true

        } else if (role === 'coin-description-object'){
          target.attr("placeholder","Object:");

          document.querySelector('[data-side="'+side+'"][data-action="simpleSpecialiseObject"]').disabled = true;
          document.querySelector('[data-side="'+side+'"][data-action="absoluteSpecialiseObject"]').disabled = true;
          document.querySelector('[data-side="'+side+'"][data-action="simpleGeneraliseObject"]').disabled = true;
          document.querySelector('[data-side="'+side+'"][data-action="absoluteGeneraliseObject"]').disabled = true;
          document.querySelector('[data-side="'+side+'"][data-action="similarObject"]').disabled = true
        }
      } else if (e.key === "Backspace" && target.val().length === 0 && searchtype === 'hierarchy') {
        cleanRecommendations(target);
        cooldown = setTimeout(() => {
        // Adaptation: we now have different recommendations functions, depending on the role a different one is used. called
          if (role === 'coin-description-subject'){
            getRecommendationsSubObj(target.val(), target, true, lastSearchType)
          } else if (role === 'coin-description-object'){
            getRecommendationsSubObj(target.val(), target, false, lastSearchType); 
          }
          
        }, 500);
        /*
        ------------------------------------------------------------------------------- (END) NEW by Nico Lambert --------------------------------------------------------
        */
      }
    }

    target.attr("data-textlength", target.val().length.toString());
  });
  
  
  $("[data-action='addKeyword']").click((e) => {
    /*
    ----------------------------------------------------------------------------- (START) UPDATE by Steven Nowak --------------------------------------------------------
    */
    // before:  $(e.currentTarget).parent() ; now  $(e.currentTarget).parent().parent() 
    // change was needed, because we addded a new div there and so the hierarchy changed
    const targetParent = $(e.currentTarget).parent().parent();
    
    const target = targetParent.children("[data-role='coin-keyword']");
    const kec = targetParent.children(".keywordContainer");
    const keywordText = target.val().trim();
    const side = targetParent.parent().attr("data-side");

    if (keywordText !== "") {
      let keyword = $("<span></span>", {
        class: "keyword",
        "data-negated": "false",
      });
      let label = $("<span></span>", { class: "label" }).text(keywordText);
      
      //Included a button to edit the keyword
      let button = $('<button></button>', {
        class: "editKeywordButton",
        html: '<i class="fa-solid fa-pencil"></i>', 
        "data-action": "editKeyword",
        "data-label": keywordText
      });
      
      /*
      ------------------------------------------------------------------------------- (END) UPDATE by Steven Nowak --------------------------------------------------------
      */
      keyword.append(label);
      keyword.append(button);
      kec.append(keyword);
      target.val("");

      const keywordObj = { text: keywordText, negated: false };

      appState.currentCoin[side].keywords.push(keywordObj);
    }
  });

 
  $("[data-action='clearInputCoin']").click((e) => {
    clearForm();
  });

  $("[data-action='clearAllQueriedCoins']").click((e) => {
    appState.clearCoins();
  });

  $("[data-action='addCoin']").click((e) => {
    addCoinToQuery();
  });

  $("[data-action='editRelation']").click((e) => {
    $("#relationMenu").toggleClass("hidden");
    $("#searchActions .searchcoin").prop("disabled", true);
  });

  $("[data-action='clearSPARQLEditor']").click((e) => {
    editor.setValue("");
  });

  $("[data-action='beautifySPARQLeditor']").click((e) => {
    editor.setValue(spfmt(editor.getValue()));
  });

  $("#relationMenu").on("click", ".coin-tr[data-id]", function (e) {
    insertAtEnd(
      createElementFromHTML(
        `<span contenteditable="false" class="id">${$(e.currentTarget).attr(
          "data-id"
        )}</span>`
      )
    );
  });

  $(".calculator-grid button[data-op]").click((e) => {
    const operation = $(e.currentTarget).attr("data-op");
    const operationHtmlMap = {
      p_open: '<span contenteditable="false" class="op p_open">&nbsp;</span>',
      p_close: '<span contenteditable="false" class="op p_close">&nbsp;</span>',
      and: '<span contenteditable="false" class="op and">&nbsp;</span>',
      or: '<span contenteditable="false" class="op or">&nbsp;</span>',
      not: '<span contenteditable="false" class="op not">&nbsp;</span>',
    };

    insertAtEnd(createElementFromHTML(operationHtmlMap[operation]));
  });

  $("#relationEditor").on("input", function () {
    appState.relationString = htmlToRelationString();

    regenerateQuery();
  });

  $(".calculator-grid button.clear").click((e) => {
    $("#relationEditor").empty();
  });

  $("#relationMenu .save").click((e) => {
    $("#relationMenu").toggleClass("hidden");
    if (appState._coins.length > 0) {
      $("#searchActions .searchcoin").prop("disabled", false);
    }
    
  });

  $("#relationMenu .close").click((e) => {
    $("#relationMenu").toggleClass("hidden");
    if (appState._coins.length > 0) {
      $("#searchActions .searchcoin").prop("disabled", false);
    }
  });

  $("#resultContainer").on("click", ".result-item", function () {
    var redirectUrl = $(this).data("redirect");

    if (redirectUrl) {
      window.open(redirectUrl, "_blank");
    }
  });

  $("[data-action=searchCoin]").click((e) => {
    appState.currentSearchType = $(e.currentTarget).attr("value");
    regenerateQuery();

    /*
    ----------------------------------------------------------------------------- (START) NEW by Nico Lambert --------------------------------------------------------
    */
    // The div with the coin results is now only displayed after clicking on the search button, before it was always visible.
    var resultBoxDiv = document.getElementById("resultBox");
    resultBoxDiv.style.display = "block";

    // query wasn not finished generating by the time the performSearch function started. To fix this we added a small delay before the function begins the search
    setTimeout(() => {
      performSearch();
    }, 100); 
    /*
    ------------------------------------------------------------------------------- (END) NEW by Nico Lambert --------------------------------------------------------
    */
  });

  $("[data-action=downloadResults]").click((e) => {
    e.preventDefault();

    var data = {
      action: "download",
      fileType: "csv",
      searchType: appState.currentSearchType,
      q: editor.getValue(),
    };

    var form = $("<form>", {
      method: "POST",
      action: "/callback",
    }).css({
      display: "none",
    });

    $.each(data, function (key, value) {
      form.append(
        $("<input>", {
          type: "hidden",
          name: key,
          value: value,
        })
      );
    });

    $("body").append(form);
    form.submit();
    form.remove();
  });


  $("#sortSelect, #sortDirection, #groupSelect").change(function () {
    sortResults();
    appState.renderCurrentPage();
  });

  $("#returnToQuery").click(function () {
    $("#moveableStage").attr("data-state", "query");

    /*
    ----------------------------------------------------------------------------- (START) NEW by Nico Lambert --------------------------------------------------------
    */
    // After the user clicks on the "Return to query" button, the result box gets hidden
    // Timer , so that the result box gets not hidden while the user still sees it, it takes a while until the effect happens that the main page is displayed
    setTimeout(() => {
      
      var resultBoxDiv = document.getElementById("resultBox");
      resultBoxDiv.style.display = "none";
      
    },1000)
    /*
    ------------------------------------------------------------------------------- (END) NEW by Nico Lambert --------------------------------------------------------
    */
    

  });

  $("#prevPage").click(function () {
    appState.previousPage();
  });

  $("#nextPage").click(function () {
    appState.nextPage();
  });


/**
 * Function that checks if hierachy buttons for a search field should be active or deactive based on if the buttons effect the return at least one recommendation 
 * 
 * @param {String} side - side of the inputs fields for which the function is performed
 * @returns {void}
 * 
 * Author: Nico Lambert
 * Updated by Steven Nowak
 * Now include equivalent Hierachy and works faster through streamlining of the SPARQL Queries 
 */
function disableHierarchyButtons(side){
  let subj_uri = ""
  let pred_uri = ""
  let obj_uri = ""
  //Extracts subject predicate and object URI's from current coin
  for (let i = 0 ; i < appState.currentCoin[side].coin.length; i++) {
    if (appState.currentCoin[side].coin[i].type === "Subj") {
      subj_uri = appState.currentCoin[side].coin[i].item.link 
    } else if (appState.currentCoin[side].coin[i].type === "Obj") {
      obj_uri = appState.currentCoin[side].coin[i].item.link 
    } else {
      pred_uri = appState.currentCoin[side].coin[i].item.link 
    }
  }
  
  //Changes URI's into a format usable in SPARQL Querries  
  if (subj_uri == ""){
    subj_uri = "?s"
  }else{
    subj_uri = "<"+subj_uri+">"
  }
        
  if (pred_uri == ""){
    pred_uri = "?p"
  }else{
    pred_uri = "<"+pred_uri+">"
  }
    
  if (obj_uri == ""){
    obj_uri = "?o" 
  }else{
    obj_uri = "<"+obj_uri+">"
  }

  // Steven Nowak adapting if check 
  // (now one for subject and one for object (because maybe through the changed entity also the buttons of the other triple element have to be disabled / enabled)) 

  if (subj_uri != "?s"){
    if(pred_uri == "?p" && obj_uri == "?o"){      
      //Request that checks if at least one recommandation exists for predicate and object based on the current subject
      //Reason: Subjects when not connected with a predicate or object can also be singular entities that appear on a coin but do not exist in a triple relation with any othere URI   
      $.ajax({
        method: "POST",
        url: "callback",
        data: {
          action: "areRecommendationsAvailable",
          subj_uri: subj_uri,
          side: side,
        },
        success: function (r) {
          appState.latestResponse = r.result;
          if (r.success) {
            if (r.result == "true"){
              document.querySelector('[data-side="'+side+'"][data-action="listAllPredicates"]').disabled = false;
              document.querySelector('[data-side="'+side+'"][data-action="listAllObj"]').disabled = false;  
            }else{
              document.querySelector('[data-side="'+side+'"][data-action="listAllPredicates"]').disabled = true;
              document.querySelector('[data-side="'+side+'"][data-action="listAllObj"]').disabled = true;
            }
          }
          onComplete();
        },
      });
    }
    //Request that checks if at least one recommandation exists for the generalisation of the current subject
    $.ajax({
      method: "POST",
      url: "callback",
      data: {
        action: "areGeneraliseRecommendationsAvailable",
        q: subj_uri.substring(1, subj_uri.length - 1),
        subj_uri: subj_uri,
				pred_uri: pred_uri,
				obj_uri: obj_uri,
				is_subject: "true", 
				side: side,
      },
      success: function (r) {
        appState.latestResponse = r.result;
        
        if (r.success) {
          
          if (r.result == "true"){
            document.querySelector('[data-side="'+side+'"][data-action="simpleGeneraliseSubject"]').disabled = false;
            document.querySelector('[data-side="'+side+'"][data-action="absoluteGeneraliseSubject"]').disabled = false;
          }else{
            document.querySelector('[data-side="'+side+'"][data-action="simpleGeneraliseSubject"]').disabled = true;
            document.querySelector('[data-side="'+side+'"][data-action="absoluteGeneraliseSubject"]').disabled = true;
          }
        }
  
        onComplete();
      },
    });
    //Request that checks if at least one recommandation exists for the specialisation of the current subject
    $.ajax({
      method: "POST",
      url: "callback",
      data: {
        action: "areSpecialiseRecommendationsAvailable",
        q: subj_uri.substring(1, subj_uri.length - 1),
        subj_uri: subj_uri,
        pred_uri: pred_uri,
        obj_uri: obj_uri,
        is_subject: "true",
        side: side,
      },
      success: function (r) {
       
        appState.latestResponse = r.result;
        
        if (r.success) {
          if (r.result == "true"){
            document.querySelector('[data-side="'+side+'"][data-action="simpleSpecialiseSubject"]').disabled = false;
            document.querySelector('[data-side="'+side+'"][data-action="absoluteSpecialiseSubject"]').disabled = false;
          }else{
            document.querySelector('[data-side="'+side+'"][data-action="simpleSpecialiseSubject"]').disabled = true;
            document.querySelector('[data-side="'+side+'"][data-action="absoluteSpecialiseSubject"]').disabled = true;
          }
        }
        onComplete();
      },
    });
    /*
    ----------------------------------------------------------------------- (START) UPDATE by Steven Nowak --------------------------------------------------------
    */
    //Request that checks if at least one recommandation exists for equivalent entities of the current subject
    $.ajax({
      method: "POST",
      url: "callback",
      data: {
        action: "areEquivalentRecommendationsAvailable",
        q: subj_uri.substring(1, subj_uri.length - 1),
        subj_uri: subj_uri,
        pred_uri: pred_uri,
        obj_uri:obj_uri,
        is_subject: "true",
        side: side,
      },
      success: function (r) {
        appState.latestResponse = r.result;
        if (r.success) {
          if (r.result == "true"){
            document.querySelector('[data-side="'+side+'"][data-action="similarSubject"]').disabled = false; 
          }else{
            document.querySelector('[data-side="'+side+'"][data-action="similarSubject"]').disabled = true;
          }
        }
        onComplete();
      },
    });
    /*
    ----------------------------------------------------------------------- (END) UPDATE by Steven Nowak --------------------------------------------------------
    */
  } else {
    if (pred_uri == "?p"){
      document.querySelector('[data-side="'+side+'"][data-action="listAllPredicates"]').disabled = false;
    }
    if (obj_uri == "?o"){
      document.querySelector('[data-side="'+side+'"][data-action="listAllObj"]').disabled = false;
    }
  }
  if (obj_uri != "?o"){
    //Request that checks if at least one recommandation exists for the generalisation of the current object
    $.ajax({
      method: "POST",
      url: "callback",
      data: {
        action: "areGeneraliseRecommendationsAvailable",
        q: obj_uri.substring(1, obj_uri.length - 1),
        subj_uri: subj_uri,
				pred_uri: pred_uri,
				obj_uri: obj_uri,
				is_subject: "false", 
				side: side,
      },
      success: function (r) {
        appState.latestResponse = r.result;
        
        if (r.success) {
          
          if (r.result == "true"){
            document.querySelector('[data-side="'+side+'"][data-action="simpleGeneraliseObject"]').disabled = false;
            document.querySelector('[data-side="'+side+'"][data-action="absoluteGeneraliseObject"]').disabled = false;
          }else{
            document.querySelector('[data-side="'+side+'"][data-action="simpleGeneraliseObject"]').disabled = true;
            document.querySelector('[data-side="'+side+'"][data-action="absoluteGeneraliseObject"]').disabled = true;
          }
        }
  
        onComplete();
      },
    });
    //Request that checks if at least one recommandation exists for the specialisation of the current object
    $.ajax({
      method: "POST",
      url: "callback",
      data: {
        action: "areSpecialiseRecommendationsAvailable",
        q: obj_uri.substring(1, obj_uri.length - 1),
        subj_uri: subj_uri,
        pred_uri: pred_uri,
        obj_uri: obj_uri,
        is_subject: "false",
        side: side,
      },
      success: function (r) {
        appState.latestResponse = r.result;
        
        if (r.success) {
          if (r.result == "true"){
            document.querySelector('[data-side="'+side+'"][data-action="simpleSpecialiseObject"]').disabled = false;
            document.querySelector('[data-side="'+side+'"][data-action="absoluteSpecialiseObject"]').disabled = false;
          }else{
            document.querySelector('[data-side="'+side+'"][data-action="simpleSpecialiseObject"]').disabled = true;
            document.querySelector('[data-side="'+side+'"][data-action="absoluteSpecialiseObject"]').disabled = true;
          }
        }
        onComplete();
      },
    });
   //Request that checks if at least one recommandation exists for equivalent entities of the current object
    $.ajax({
      method: "POST",
      url: "callback",
      data: {
        action: "areEquivalentRecommendationsAvailable",
        q: obj_uri.substring(1, obj_uri.length - 1),
        subj_uri: subj_uri,
        pred_uri: pred_uri,
        obj_uri: obj_uri,
        is_subject: "false",
        side: side,
      },
      success: function (r) {
        appState.latestResponse = r.result;
        if (r.success) {
          if (r.result == "true"){
            document.querySelector('[data-side="'+side+'"][data-action="similarObject"]').disabled = false; 
          }else{
            document.querySelector('[data-side="'+side+'"][data-action="similarObject"]').disabled = true;
          }
        }
  
        onComplete();
      },
    });
  }

}  





/*
----------------------------------------------------------------------------- (START) NEW by Nico Lambert --------------------------------------------------------
*/
// 
$("[data-action ^='listAll']").click((e) => {
  const target = $(e.currentTarget);
  const side = target.data('side')
  const action = target.data('action')
  if (action == "listAllPredicates"){

    let element = document.getElementById("predicate"+side)
    // If recommendations already exist for the user , the next click on the button folds it back in  
    // otherwise the user gets all current possible predicates for the current side as recommendations
    if (element) {
      cleanRecommendations(target);
    }else{
      target.parent().parent().children(".textbox").val("");
      target.parent().parent().children(".textbox").attr("placeholder", "Predicate:");
      getRecommendationsPredicate(target.val(), target.parent(), "standard", side);
    }

  } else if (action == "listAllSubj"){

    // If recommendations already exist for the user , the next click on the button folds it back in  
    // otherwise the user gets all current possible subjects for the current side as recommendations
    let element = document.getElementById("subjecttrue"+side)
    if (element) {
      cleanRecommendations(target);
    }else{
      target.parent().parent().parent().children(".textbox").val("");
      target.parent().parent().parent().children(".textbox").attr("placeholder", "Subject:");
      getRecommendationsSubObj("", $('[data-role="coin-description-subject"][data-side="'+side+'"][data-searchtype="standard"]'), true, "standard"); 
    }

  } else{

    // If recommendations already exist for the user , the next click on the button folds it back in  
    // otherwise the user gets all current possible objects for the current side as recommendations
    let element = document.getElementById("subjectfalse"+side)
    if (element) {
      cleanRecommendations(target);
    }else{
      target.parent().parent().parent().children(".textbox").val("");
      target.parent().parent().parent().children(".textbox").attr("placeholder", "Object:");
      getRecommendationsSubObj("", $('[data-role="coin-description-object"][data-side="'+side+'"][data-searchtype="standard"]'), false, "standard"); 
    }

  }
  cleanHierachy();
});


//Cancels active hierarchy search
$("[data-action='backToStandardSearch']").click((e) => {
    cleanHierachy();
});

//Triggers hierachy search function for singular generalisation and singular specialisation
// -> standard search field is hidden , hierachy search field is shown
//Reason: Split for buttons because of easier positioning in .css 
$("[data-action^='simple']").click((e) => {
  cleanHierachy();
  const target = $(e.currentTarget);
  const action = target.data('action'); 
  const side = target.data('side');
  if (action =='simpleGeneraliseSubject') {
    document.getElementById("hierarchySearch-" + side + "-subject").style.display = "flex";
    document.getElementById("standardSearch-" + side + "-subject").style.display = "none";
    getRecommendationsSubObj("", $('[data-role="coin-description-subject"][data-side="'+side+'"][data-searchtype="hierarchy"]'), true, "hierarchy-generalise-simple"); 
    lastSearchType = "hierarchy-generalise-simple";
  } else if (action =='simpleGeneraliseObject') {
    document.getElementById("hierarchySearch-" + side + "-object").style.display = "flex";
    document.getElementById("standardSearch-" + side + "-object").style.display = "none";
    getRecommendationsSubObj("", $('[data-role="coin-description-object"][data-side="'+side+'"][data-searchtype="hierarchy"]'), false, "hierarchy-generalise-simple"); 
    lastSearchType = "hierarchy-generalise-simple";
  } else if (action =='simpleSpecialiseSubject') {
    document.getElementById("hierarchySearch-" + side + "-subject").style.display = "flex";
    document.getElementById("standardSearch-" + side + "-subject").style.display = "none";
    getRecommendationsSubObj("", $('[data-role="coin-description-subject"][data-side="'+side+'"][data-searchtype="hierarchy"]'), true, "hierarchy-specialise-simple"); 
    lastSearchType = "hierarchy-specialise-simple";
  } else if (action =='simpleSpecialiseObject') {
    document.getElementById("hierarchySearch-" + side + "-object").style.display = "flex";
    document.getElementById("standardSearch-" + side + "-object").style.display = "none";
    getRecommendationsSubObj("", $('[data-role="coin-description-object"][data-side="'+side+'"][data-searchtype="hierarchy"]'), false, "hierarchy-specialise-simple"); 
    lastSearchType = "hierarchy-specialise-simple";
  }
  
  
});

//Triggers hierachy search function for absolute generalisation and absolute specialisation
// -> standard search field is hidden , hierachy search field is shown
//Reason: Split for buttons because of easier positioning in .css 
$("[data-action^='absolute']").click((e) => {
  cleanHierachy();
  const target = $(e.currentTarget);
  const action = target.data('action'); 
  const side = target.data('side');


  if (action =='absoluteGeneraliseSubject') {
    document.getElementById("hierarchySearch-" + side + "-subject").style.display = "flex";
    document.getElementById("standardSearch-" + side + "-subject").style.display = "none";
    getRecommendationsSubObj("", $('[data-role="coin-description-subject"][data-side="'+side+'"][data-searchtype="hierarchy"]'), true, "hierarchy-generalise-absolute"); 
    lastSearchType = "hierarchy-generalise-absolute";
  } else if (action =='absoluteGeneraliseObject') {
    document.getElementById("hierarchySearch-" + side + "-object").style.display = "flex";
    document.getElementById("standardSearch-" + side + "-object").style.display = "none";
    getRecommendationsSubObj("", $('[data-role="coin-description-object"][data-side="'+side+'"][data-searchtype="hierarchy"]'), false, "hierarchy-generalise-absolute"); 
    lastSearchType = "hierarchy-generalise-absolute";
  } else if (action =='absoluteSpecialiseSubject') {
    document.getElementById("hierarchySearch-" + side + "-subject").style.display = "flex";
    document.getElementById("standardSearch-" + side + "-subject").style.display = "none";
    getRecommendationsSubObj("", $('[data-role="coin-description-subject"][data-side="'+side+'"][data-searchtype="hierarchy"]'), true, "hierarchy-specialise-absolute"); 
    lastSearchType = "hierarchy-specialise-absolute";
    
  } else if (action =='absoluteSpecialiseObject') {
    document.getElementById("hierarchySearch-" + side + "-object").style.display = "flex";
    document.getElementById("standardSearch-" + side + "-object").style.display = "none";
    getRecommendationsSubObj("", $('[data-role="coin-description-object"][data-side="'+side+'"][data-searchtype="hierarchy"]'), false, "hierarchy-specialise-absolute"); 
    lastSearchType = "hierarchy-specialise-absolute";
  }
  
});

//Triggers equivalent hierachy search function
// -> standard search field is hidden , hierachy search field is shown
//Reason: Split for buttons because of easier positioning in .css 
$("[data-action^='similar']").click((e) => {
  cleanHierachy();
  const target = $(e.currentTarget);
  const action = target.data('action'); 
  const side = target.data('side');

  if (action =='similarSubject') {
    document.getElementById("hierarchySearch-" + side + "-subject").style.display = "flex";
    document.getElementById("standardSearch-" + side + "-subject").style.display = "none";
    getRecommendationsSubObj("", $('[data-role="coin-description-subject"][data-side="'+side+'"][data-searchtype="hierarchy"]'), true, "hierarchy-equivalent"); 
    lastSearchType = "hierarchy-equivalent";
  } else if (action =='similarObject') {
    document.getElementById("hierarchySearch-" + side + "-object").style.display = "flex";
    document.getElementById("standardSearch-" + side + "-object").style.display = "none";
    getRecommendationsSubObj("", $('[data-role="coin-description-object"][data-side="'+side+'"][data-searchtype="hierarchy"]'), false, "hierarchy-equivalent"); 
    lastSearchType = "hierarchy-equivalent";
  } 
  
});
/*
------------------------------------------------------------------------------- (END) NEW by Nico Lambert --------------------------------------------------------
*/



/*
----------------------------------------------------------------------------- (START) NEW by Steven Nowak --------------------------------------------------------
*/
// Buttons that directly adds a keyword in negated form (Based on existing addKeyword action)
$("[data-action='negateKeyword']").click((e) => {
  const targetParent = $(e.currentTarget).parent().parent();
  const target = targetParent.children("[data-role='coin-keyword']");
  const kec = targetParent.children(".keywordContainer");
  const keywordText = target.val().trim();
  const side = targetParent.parent().attr("data-side");

  if (keywordText !== "") {
    let keyword = $("<span></span>", {
      class: "keyword",
      "data-negated": "true",
    });
    let label = $("<span></span>", { class: "label" }).text(keywordText);

    //Included a button to edit the keyword
    let button = $('<button></button>', {
      class: "editKeywordButton",
      html: '<i class="fa-solid fa-pencil"></i>', 
      "data-action": "editKeyword",
      "data-label": keywordText
    });
    

    keyword.append(label);
    keyword.append(button);
    kec.append(keyword);
    target.val("");

    const keywordObj = { text: keywordText, negated: true };

    appState.currentCoin[side].keywords.push(keywordObj);
  }
});

//Function that takes the keyword and adds it back to the input field while at the same time deleting it from the keyword container
$(document).on("click", "[data-action='editKeyword']", (e) => {
  const target = $(e.currentTarget);
  const side = target.data('side');
  const label = target.data('label');
  const inputField = target.parent().parent().parent().children("[data-role='coin-keyword']");
  inputField.val(label);
  if (side == "obverse") {
    for (let i = 0; i < appState.currentCoin.obverse.keywords.length; i++) {
      if (appState.currentCoin.obverse.keywords[i].text == label) {
        appState.currentCoin.obverse.keywords.splice(i, 1);
        break;
      }
    }  
  } else {
    for (let i = 0; i < appState.currentCoin.reverse.keywords.length; i++) {
      if (appState.currentCoin.reverse.keywords[i].text == label) {
        appState.currentCoin.reverse.keywords.splice(i, 1);
        break;
      }
    }  
  }
  target.parent().remove();

});

//Clears any text inside the keyword input field
$("[data-action='clearKeyword']").click((e) => {
  const targetParent = $(e.currentTarget).parent().parent();
  targetParent.find('input[type="text"]').val('');

});

/*
------------------------------------------------------------------------------- (END) NEW by Steven Nowak --------------------------------------------------------
*/


});






