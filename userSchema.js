const mongoose = require("mongoose");

const userSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true,
    validate: {
      validator: function(value) {
        return value.length >= 2 && value.length <= 50;
      },
      message: "Name should be atleast 2 and 50 characters long."
    }
  },
    
  
phone : {
  required: true,
  type: Number,
  validate: {
    validator: function(v) {
      console.log(v," testing ")
      return `${v}`.length === 10 ;

    },
    message: '{VALUE} is not a valid 10 digit number!'
}
},
address : {
  type: String,
  required:true,
  type: String,
  required: true,
  validate: {
    validator: function(value) {
      return value.length >= 5 && value.length <= 100;
    },
    message: "Address should be between 5 and 100 characters long."
  }
},

card : {
  type: String,
  validate: {
    validator: function(v) {
      console.log(v," testing ")
      return `${v}`.length === 4 ;

    },
    message: 'Should be atleast 4 digits!'
}
},
card_month : {
  type: Number,
  validate: {
    validator: function(v) {
      console.log(v," testing ")
      return `${v}`.length === 2 ;

    },
    message: '{VALUE} is not a valid 2 digit number!'
}
},
card_year : {
  type: Number,
  validate: {
    validator: function(v) {
      console.log(v," testing ")
      return `${v}`.length === 4 ;

    },
    message: '{VALUE} is not a valid 4 digit number!'
}
},
card_cvv : {
  type: Number,
  validate: {
    validator: function(v) {
      console.log(v," testing ")
      return `${v}`.length === 3 ;

    },
    message: '{VALUE} is not a valid 3 digit number!'
}
},
});

const User = mongoose.model("users", userSchema);

module.exports = User;