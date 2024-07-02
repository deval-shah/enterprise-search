import { getTokens } from "next-firebase-auth-edge";
import { cookies } from "next/headers";
import { notFound } from "next/navigation";
import { clientConfig, serverConfig } from "../config";
import HomePage from "./HomePage";
import Image from "next/image";

export default async function Home() {
  // console.log("Cookies:", cookies());
  // console.log("Config:", {
  //   apiKey: clientConfig.apiKey,
  //   cookieName: serverConfig.cookieName,
  //   cookieSignatureKeys: serverConfig.cookieSignatureKeys,
  //   serviceAccount: serverConfig.serviceAccount,
  // });

  const tokens = await getTokens(cookies(), {
    apiKey: clientConfig.apiKey,
    cookieName: serverConfig.cookieName,
    cookieSignatureKeys: serverConfig.cookieSignatureKeys,
    serviceAccount: serverConfig.serviceAccount,
  });
  console.log("Tokens:", tokens);
  if (!tokens) {
    notFound();
  }

  return <HomePage email={tokens?.decodedToken.email} />;
}
