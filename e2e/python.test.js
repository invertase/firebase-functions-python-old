const { initializeApp } = require("firebase/app");
const { getAuth, signInAnonymously } = require("firebase/auth");
const { httpsCallable, getFunctions } = require("firebase/functions");

const config = {
  apiKey: "AIzaSyCZ2C2_0jQIkQItbiJ4IGbL8OLObbK2mY0",
  authDomain: "python-functions-testing.firebaseapp.com",
  projectId: "python-functions-testing",
  storageBucket: "python-functions-testing.appspot.com",
  messagingSenderId: "441947996129",
  appId: "1:441947996129:web:227004b738ba64f04edca0",
  measurementId: "G-243GFNMBFV",
};

describe("firebase-functions-python", () => {
  let instance;
  let unauthenticatedInstance;

  // Initialize the app before running any tests.
  // Default app is authenticated.
  beforeAll(async () => {
    const app = initializeApp(config);
    const unauthenticatedApp = initializeApp(config);
    await signInAnonymously(getAuth(app));

    instance = getFunctions(app);
    unauthenticatedInstance = getFunctions(unauthenticatedApp);
  });

  // test("accepts a primitive arg of `undefined`", () => {
  //   const callable = httpsCallable(instance, "testfunctiondefaultregion");
  //   const { data } = await callable();
  //   expect(data).toBe('None');
  // });

  test("accepts a primitive arg of `string`", async () => {
    const callable = httpsCallable(instance, "testfunctiondefaultregion");
    const { data } = await callable('foo');
    expect(data).toBe('string');
  });

  test("accepts a primitive arg of `number`", async () => {
    const callable = httpsCallable(instance, "testfunctiondefaultregion");
    const { data } = await callable(123);
    expect(data).toBe('number');
  });

  test("accepts a primitive arg of `boolean`", async() => {
    const callable = httpsCallable(instance, "testfunctiondefaultregion");
    const { data } = await callable(true);
    expect(data).toBe('boolean');
  });

  test("accepts a primitive arg of `null`", async () => {
    const callable = httpsCallable(instance, "testfunctiondefaultregion");
    const { data } = await callable(null);
    expect(data).toBe('None');
  });

  test("accepts an arg of `array`", async () => {
    const callable = httpsCallable(instance, "testfunctiondefaultregion");
    const { data } = await callable([1, '2', true]);
    expect(data).toBe('array');
  });

  test("accepts an arg of `object`", async () => {
    const callable = httpsCallable(instance, "testfunctiondefaultregion");
    const { data } = await callable({ foo: 'bar' });
    expect(data).toBe('object');
  });
});
