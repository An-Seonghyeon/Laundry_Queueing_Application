/**
 * Import function triggers from their respective submodules:
 *
 * const {onCall} = require("firebase-functions/v2/https");
 * const {onDocumentWritten} = require("firebase-functions/v2/firestore");
 *
 * See a full list of supported triggers at https://firebase.google.com/docs/functions
 */

const {onRequest} = require("firebase-functions/v2/https");
const functions = require("firebase-functions");
const admin = require("firebase-admin");
const logger = require("firebase-functions/logger");

// Initialize Firebase Admin SDK
admin.initializeApp();

// Create and deploy your first functions
// https://firebase.google.com/docs/functions/get-started

// exports.helloWorld = onRequest((request, response) => {
//   logger.info("Hello logs!", {structuredData: true});
//   response.send("Hello from Firebase!");
// });

exports.scheduledFunction = functions.pubsub.schedule('every 1 minutes').onRun(async (context) => {
    const now = admin.firestore.Timestamp.now();
    const waitingRef = admin.firestore().collection('waiting');
    const querySnapshot = await waitingRef.where('left_time', '<=', now.seconds).get();

    querySnapshot.forEach(doc => {
        doc.ref.delete().then(() => {
            console.log(`Deleted document with ID: ${doc.id}`);
        }).catch(error => {
            console.error(`Error deleting document: ${error}`);
        });
    });

    return null;
});
