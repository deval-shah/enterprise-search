import { initializeApp } from 'firebase/app';
import { clientConfig } from '../../config';
import { getAuth } from 'firebase/auth';

export const app = initializeApp(clientConfig);
export const auth = getAuth(app);