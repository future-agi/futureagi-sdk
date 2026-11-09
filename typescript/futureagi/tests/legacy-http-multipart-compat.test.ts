import axios from 'axios';
import { HttpClient } from '../src/api/auth';
import { HttpMethod } from '../src/api/types';

it.each(['blob', 'text'])('preserves native multipart %s inputs without Node streams', async kind => {
    const originalAdapter = axios.defaults.adapter;
    const contents = 'Synthetic native multipart content.\n';
    const adapter = jest.fn(async config => {
        const part = config.data.get('file0');
        if (kind === 'blob') {
            expect(part).toBeInstanceOf(Blob);
            expect(await part.text()).toBe(contents);
        } else {
            expect(part).toBe(contents);
        }
        expect(config.data.get('name')).toBe('docs');
        const bytes = Buffer.from(await new Response(config.data).arrayBuffer());
        expect(bytes.includes(Buffer.from(contents))).toBe(true);
        return { status: 200, statusText: 'OK', headers: {}, config, data: {} };
    });
    axios.defaults.adapter = adapter;
    const client = new HttpClient({ baseUrl: 'https://sdk.invalid', retryAttempts: 1 });
    try {
        await client.request({
            method: HttpMethod.POST,
            url: '/upload',
            files: { file0: kind === 'blob' ? new Blob([contents]) : contents },
            data: { name: 'docs' }
        });
        expect(adapter).toHaveBeenCalledTimes(1);
    } finally {
        await client.close();
        axios.defaults.adapter = originalAdapter;
    }
});
