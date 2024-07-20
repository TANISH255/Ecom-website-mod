const express = require('express')
const mongoose = require('mongoose')

const app = express();
const userModel = require('./userSchema')
app.use(express.json());
app.use(express.urlencoded({extended: true}))
app.use(express.static('public'))

mongoose.connect('mongodb+srv://waghuletanish767:HRujMnb1jAK2DIsS@cluster0.zs4ydim.mongodb.net/mydb?retryWrites=true&w=majority', {
  useNewUrlParser: true,
    
    useUnifiedTopology: true
})

app.get('/', (req,res) => {
  res.sendFile('public/index.html')
})

app.post('/post', async (req,res)=> {
  

  try {
    await userModel.create(req.body) 
    res.send({ status: 'success' })
    }catch(err) {
    res.send({ error : err.message})
    }
})
app.listen(3000, () => {
  console.log('server started on 3000')
})

