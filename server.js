require('dns').setServers(['8.8.8.8', '8.8.4.4'])
require('dotenv').config()
const express = require('express')
const mongoose = require('mongoose')
const path = require('path')

const app = express()
const userModel = require('./userSchema')
app.use(express.json())
app.use(express.urlencoded({ extended: true }))
app.use(express.static('public'))

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'))
})

app.post('/post', async (req, res) => {
  try {
    await userModel.create(req.body)
    res.send({ status: 'success' })
  } catch (err) {
    res.send({ error: err.message })
  }
})

const mongoUri = new URL(process.env.MONGO_URI)
mongoUri.username = 'appuser'
mongoUri.password = process.env.ATLAS_USER_PASS

mongoose.connect(process.env.MONGO_URI)
  .then(() => console.log('MongoDB connected'))
  .catch(err => console.error('MongoDB connection error:', err.message))

const PORT = process.env.PORT || 3000
app.listen(PORT, () => console.log(`server started on ${PORT}`))