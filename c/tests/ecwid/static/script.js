const Ecwid = {
    OnAPILoaded: {
        add: function(f){
            f();
        }
    },
    OnOrderPlaced: {
        add: function(){}
    },
    Cart: {
        setCustomerEmail: function(){},
        setOrderComments: function(){}
    }
};
const ec = {};
function xProductBrowser(param1, param2, param3, param4, param5) {
    let storeDiv = $("["+param5+"]");
    storeDiv.text("TEST ECWID STORE");
    storeDiv.addClass("text-center font-weight-bold h1")
}