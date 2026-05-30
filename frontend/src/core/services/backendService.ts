export async function checkBackendHealth() {

    try {

        const response = await fetch(
            'http://127.0.0.1:8000/health'
        )

        return response.ok

    } catch {

        return false
    }
}